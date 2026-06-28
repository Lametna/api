from typing import List, Optional
from django.contrib.auth import get_user_model
from .models import Rule, FeatureFlag

User = get_user_model()

class RuleSelector:
    @staticmethod
    def get_active_rules_for_event(event_name: str) -> List[Rule]:
        """Fetch all active rules that trigger on this specific event name."""
        return list(Rule.objects.filter(is_active=True, trigger_event=event_name).prefetch_related('actions'))

class FeatureFlagSelector:
    @staticmethod
    def get_all_flags() -> List[FeatureFlag]:
        return list(FeatureFlag.objects.all().prefetch_related('segments'))

    @staticmethod
    def get_flag(key: str) -> Optional[FeatureFlag]:
        return FeatureFlag.objects.filter(flag_key=key).prefetch_related('segments').first()
