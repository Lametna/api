import json
from typing import Dict, Any, List
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Rule, FeatureFlag
from .selectors import RuleSelector, FeatureFlagSelector
from apps.common.events import BaseDomainEvent, EventDispatcher, RewardGrantedEvent

User = get_user_model()

class RuleProcessorService:
    @staticmethod
    def evaluate_event(event: BaseDomainEvent) -> None:
        """
        Dynamically intercepts an event, evaluates rules, and fires actions.
        """
        event_name = event.__class__.__name__
        rules = RuleSelector.get_active_rules_for_event(event_name)
        
        # Convert event payload to dict for condition checking
        event_dict = event.__dict__
        
        for rule in rules:
            if RuleProcessorService._evaluate_condition(rule.condition_payload, event_dict):
                RuleProcessorService._execute_actions(rule, event_dict)

    @staticmethod
    def _evaluate_condition(condition: Dict[str, Any], event_dict: Dict[str, Any]) -> bool:
        """
        Simple deterministic condition evaluation.
        MVP: checks if the event payload matches the exact key-value pairs in the condition.
        E.g. condition: {"is_ranked": True}, event: {"is_ranked": True} -> Match.
        """
        if not condition:
            return True # Empty condition always fires
            
        for key, expected_val in condition.items():
            if key == "day_of_week":
                if timezone.now().strftime('%A').upper() != expected_val:
                    return False
            elif event_dict.get(key) != expected_val:
                return False
        return True

    @staticmethod
    def _execute_actions(rule: Rule, event_dict: Dict[str, Any]) -> None:
        """
        Execute actions by emitting secondary events to maintain Clean Architecture.
        """
        for action in rule.actions.all():
            if action.action_type == 'GRANT_REWARD_MULTIPLIER':
                # Example: Emitting a secondary Reward event based on the rule
                player_id = event_dict.get('player_id')
                if player_id:
                    multiplier = action.action_payload.get('multiplier', 1.0)
                    base_amount = event_dict.get('amount', 100) # Fallback heuristic
                    bonus_amount = int(base_amount * multiplier) - base_amount
                    
                    if bonus_amount > 0:
                        # Dispatch a secondary reward event completely decoupled from the original!
                        EventDispatcher.publish(RewardGrantedEvent(
                            player_id=player_id, reward_id=str(bonus_amount), reward_type='COINS'
                        ))

class FeatureFlagService:
    @staticmethod
    def is_enabled(flag_key: str, user: User = None) -> bool:
        flag = FeatureFlagSelector.get_flag(flag_key)
        if not flag:
            return False
            
        if flag.is_global_enabled:
            return True
            
        if not user:
            return False
            
        for segment in flag.segments.filter(is_active=True):
            if segment.condition_type == 'USER_ID' and str(user.id) == segment.condition_value:
                return True
            # if segment.condition_type == 'COUNTRY' and user.profile.country == segment.condition_value:
            #    return True
                
        return False
        
    @staticmethod
    def get_all_flags_for_user(user: User) -> Dict[str, bool]:
        flags = FeatureFlagSelector.get_all_flags()
        return {flag.flag_key: FeatureFlagService.is_enabled(flag.flag_key, user) for flag in flags}
