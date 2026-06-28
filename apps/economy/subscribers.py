import logging
from django.contrib.auth import get_user_model
from apps.common.events import EventDispatcher, RewardGrantedEvent
from .services import WalletService, InventoryService
from .selectors import CatalogSelector

logger = logging.getLogger(__name__)
User = get_user_model()

class EconomySubscriber:
    """
    Subscribes to Progression system rewards.
    If Progression grants a reward (like COINS or an ITEM), the Economy Engine
    intercepts the event and physically injects it into the Wallet/Inventory.
    """
    
    @staticmethod
    def setup():
        EventDispatcher.subscribe(RewardGrantedEvent, EconomySubscriber.handle_reward_granted)

    @staticmethod
    def handle_reward_granted(event: RewardGrantedEvent):
        try:
            user = User.objects.get(id=event.player_id)
            if event.reward_type == 'COINS':
                # Reward ID represents the amount in this simplified model
                amount = int(event.reward_id)
                WalletService.credit(user, amount, "PROGRESSION_REWARD")
            elif event.reward_type == 'ITEM':
                item = CatalogSelector.get_item(event.reward_id)
                if item:
                    InventoryService.grant_item(user, item, 1, "PROGRESSION_REWARD")
        except Exception as e:
            logger.error(f"EconomyEngine failed to process reward: {e}")

# Initialize subscriptions
EconomySubscriber.setup()
