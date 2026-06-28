import logging
from apps.common.events import EventDispatcher
from .services import RuleProcessorService

logger = logging.getLogger(__name__)

class OperationsSubscriber:
    """
    The OperationsSubscriber is a global listener.
    Instead of subscribing to specific events, it hooks into the EventDispatcher's
    middleware layer (or listens to ALL events) to evaluate dynamic rules.
    """
    
    @staticmethod
    def setup():
        # In our current EventDispatcher, we don't have a wildcard '*' listener.
        # For the MVP, we will manually hook into high-value events.
        from apps.common.events import MatchFinishedEvent, AchievementUnlockedEvent
        
        EventDispatcher.subscribe(MatchFinishedEvent, OperationsSubscriber.process_event)
        EventDispatcher.subscribe(AchievementUnlockedEvent, OperationsSubscriber.process_event)

    @staticmethod
    def process_event(event):
        try:
            RuleProcessorService.evaluate_event(event)
        except Exception as e:
            logger.error(f"RuleEngine failed to evaluate event: {e}")

OperationsSubscriber.setup()
