from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseGamePlugin(ABC):
    """
    The interface every Lametna game must implement.
    The Match Engine calls these hooks as the state machine advances.
    """
    
    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique identifier, e.g., 'lametna.games.trivia'"""
        pass

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Returns name, min/max players, duration, etc. for the Game Registry."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validates the JSON configuration before the match is created."""
        pass

    @abstractmethod
    def on_match_start(self, match_id: str, players: List[str]) -> None:
        """Hook called when the match transitions to RUNNING."""
        pass

    @abstractmethod
    def on_round_start(self, match_id: str, round_id: str) -> None:
        """Hook called when a new round begins."""
        pass

    @abstractmethod
    def on_turn(self, match_id: str, player_id: str, action: Dict[str, Any]) -> bool:
        """Hook called when a player performs an action on their turn."""
        pass

    @abstractmethod
    def evaluate_win_condition(self, match_id: str) -> List[str]:
        """
        Evaluates if the match has ended.
        Returns a list of winning player IDs, or an empty list if ongoing.
        """
        pass

    @abstractmethod
    def on_match_finish(self, match_id: str) -> None:
        """Cleanup hook called when the match finishes."""
        pass
