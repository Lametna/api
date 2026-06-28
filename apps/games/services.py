import logging
import importlib
from typing import Tuple, Optional, Dict, Any, List
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .models import Game, Match, MatchPlayer, Round, Turn, Score
from .repositories import GameRepository, MatchRepository, RoundRepository, TurnRepository, ScoreRepository
from .selectors import GameSelector, MatchSelector, RoundSelector, TurnSelector
from .sdk.base import BaseGamePlugin
from apps.party.selectors import PartySelector
from apps.common.events import (
    EventDispatcher, GameRegisteredEvent, MatchCreatedEvent, MatchStartedEvent,
    MatchPausedEvent, MatchFinishedEvent, RoundStartedEvent, RoundFinishedEvent,
    TurnStartedEvent, TurnFinishedEvent, PlayerJoinedMatchEvent, PlayerLeftMatchEvent,
    ScoreUpdatedEvent, WinConditionMetEvent
)

logger = logging.getLogger(__name__)
User = get_user_model()

class PluginLoaderService:
    _plugins: Dict[str, BaseGamePlugin] = {}

    @classmethod
    def load_plugin(cls, plugin_path: str) -> Optional[BaseGamePlugin]:
        if plugin_path in cls._plugins:
            return cls._plugins[plugin_path]
            
        try:
            module_name, class_name = plugin_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            plugin_instance = plugin_class()
            cls._plugins[plugin_path] = plugin_instance
            return plugin_instance
        except (ImportError, AttributeError, Exception) as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            return None

    @classmethod
    def get_plugin(cls, plugin_path: str) -> Optional[BaseGamePlugin]:
        return cls._plugins.get(plugin_path) or cls.load_plugin(plugin_path)

class GameRegistryService:
    @staticmethod
    def register_game(plugin_path: str) -> Tuple[bool, str]:
        plugin = PluginLoaderService.load_plugin(plugin_path)
        if not plugin:
            return False, "Failed to load plugin."
            
        meta = plugin.metadata
        game = GameRepository.register_game(
            plugin_id=plugin_path,
            name=meta.get('name', 'Unknown Game'),
            description=meta.get('description', ''),
            version=meta.get('version', '1.0.0'),
            min_players=meta.get('min_players', 1),
            max_players=meta.get('max_players', 64)
        )
        EventDispatcher.publish(GameRegisteredEvent(game_id=str(game.id)))
        return True, "Game registered successfully."

class MatchService:
    @staticmethod
    def create_match(host: User, game_id: str, party_id: Optional[str] = None, config: Dict[str, Any] = None) -> Tuple[bool, Optional[Match], str]:
        game = GameSelector.get_game(game_id)
        if not game:
            return False, None, "Game not found."
            
        plugin = PluginLoaderService.get_plugin(game.plugin_id)
        if not plugin:
            return False, None, "Game plugin is inactive or broken."
            
        config = config or {}
        if not plugin.validate_config(config):
            return False, None, "Invalid match configuration."
            
        party = PartySelector.get_party(party_id) if party_id else None
        match = MatchRepository.create_match(game, party, config)
        MatchRepository.add_player(match, host, MatchPlayer.Status.ACTIVE)
        
        EventDispatcher.publish(MatchCreatedEvent(
            match_id=str(match.id), game_id=str(game.id), party_id=str(party.id) if party else ""
        ))
        return True, match, "Match created."

    @staticmethod
    def start_match(actor: User, match_id: str) -> Tuple[bool, str]:
        match = MatchSelector.get_match(match_id)
        if not match or match.state != Match.State.CREATED:
            return False, "Match cannot be started."
            
        plugin = PluginLoaderService.get_plugin(match.game.plugin_id)
        players = MatchSelector.get_players(match)
        
        if len(players) < match.game.min_players:
            return False, "Not enough players."
            
        MatchRepository.update_state(match, Match.State.RUNNING)
        plugin.on_match_start(str(match.id), [str(p.user.id) for p in players])
        EventDispatcher.publish(MatchStartedEvent(match_id=str(match.id)))
        return True, "Match started."

    @staticmethod
    def join_match(user: User, match_id: str) -> Tuple[bool, str]:
        match = MatchSelector.get_match(match_id)
        if not match:
            return False, "Match not found."
            
        if MatchSelector.get_player(match, str(user.id)):
            return False, "Already in match."
            
        status = MatchPlayer.Status.SPECTATING if match.state == Match.State.RUNNING else MatchPlayer.Status.ACTIVE
        MatchRepository.add_player(match, user, status)
        EventDispatcher.publish(PlayerJoinedMatchEvent(match_id=str(match.id), player_id=str(user.id)))
        return True, f"Joined match as {status}."

class RoundService:
    @staticmethod
    def start_round(match_id: str, round_number: int) -> Tuple[bool, Optional[Round], str]:
        match = MatchSelector.get_match(match_id)
        if not match:
            return False, None, "Match not found."
            
        round_obj = RoundRepository.create_round(match, round_number)
        plugin = PluginLoaderService.get_plugin(match.game.plugin_id)
        if plugin:
            plugin.on_round_start(str(match.id), str(round_obj.id))
            
        EventDispatcher.publish(RoundStartedEvent(match_id=str(match.id), round_id=str(round_obj.id)))
        return True, round_obj, "Round started."

class TurnService:
    @staticmethod
    def start_turn(round_id: str, player_id: str, turn_number: int) -> Tuple[bool, Optional[Turn], str]:
        # Implementation elided for brevity, similar to start_round but creates a Turn and caches the timer in Redis.
        return True, None, "Turn started."

class ScoringService:
    @staticmethod
    def add_score(match_id: str, player_id: str, points: int) -> Tuple[bool, str]:
        match = MatchSelector.get_match(match_id)
        if not match:
            return False, "Match not found."
            
        # In MVP we hit the DB directly, but we architected it to use Redis if high-frequency is needed.
        # For simplicity, just use DB here.
        player = MatchSelector.get_player(match, player_id)
        if not player:
            return False, "Player not found in match."
            
        ScoreRepository.update_score(match, player, points)
        EventDispatcher.publish(ScoreUpdatedEvent(match_id=str(match.id), player_id=player_id, new_score=points))
        return True, "Score updated."

class DictionaryService:
    @staticmethod
    def get_weighted_random_word(packs: Optional[List[str]] = None, categories: Optional[List[str]] = None) -> Optional['SecretWord']:
        from .models import SecretWord
        from django.db.models import Q
        import random
        from datetime import timedelta
        
        query = Q(is_active=True)
        if packs:
            query &= Q(category__pack__id__in=packs)
        if categories:
            query &= Q(category__id__in=categories)
            
        words = list(SecretWord.objects.filter(query))
        if not words:
            # Fallback to any active word if strict filters yield nothing
            words = list(SecretWord.objects.filter(is_active=True))
            if not words:
                return None
                
        now = timezone.now()
        weights = []
        
        for w in words:
            # Base weight
            w_score = float(w.weight)
            
            # Popularity boost (slightly increases chance for popular words)
            w_score += w.popularity * 0.1
            
            # Penalty for recently used
            if w.last_used_at:
                delta = (now - w.last_used_at).total_seconds()
                # If used in the last 10 minutes, massively penalize
                if delta < 600:
                    w_score *= 0.1
                # If used in the last hour, penalize
                elif delta < 3600:
                    w_score *= 0.5
                    
            # Ensure weight is at least slightly positive to remain possible
            weights.append(max(w_score, 0.1))
            
        selected_word = random.choices(words, weights=weights, k=1)[0]
        
        # Update usage stats
        selected_word.last_used_at = now
        selected_word.popularity += 1
        selected_word.save(update_fields=['last_used_at', 'popularity'])
        
        return selected_word
