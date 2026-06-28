from typing import Dict, Any
from .models import Rule, RuleAction, FeatureFlag, FeatureSegment

class OperationsRepository:
    # Most rules and flags are read-heavy, so the repository is minimal for mutations.
    # We leave these here for future administrative CRUD operations.
    
    @staticmethod
    def create_feature_flag(key: str, description: str, global_enabled: bool = False) -> FeatureFlag:
        return FeatureFlag.objects.create(flag_key=key, description=description, is_global_enabled=global_enabled)
        
    @staticmethod
    def add_segment_to_flag(flag: FeatureFlag, c_type: str, c_value: str) -> FeatureSegment:
        return FeatureSegment.objects.create(flag=flag, condition_type=c_type, condition_value=c_value)
