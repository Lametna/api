import pytest
from django.contrib.auth import get_user_model
from apps.users.services import PrivacyService
from apps.users.models import UserPrivacy

User = get_user_model()

@pytest.mark.django_db
class TestPrivacyService:
    def test_apply_visibility_rules_private_profile(self):
        owner = User.objects.create_user(username='owner', email='o@o.com', password='pwd')
        viewer = User.objects.create_user(username='viewer', email='v@v.com', password='pwd')
        
        privacy = UserPrivacy(user=owner, profile_visibility='PRIVATE')
        raw_data = {"country": "US", "display_name": "Test"}
        
        masked = PrivacyService.apply_visibility_rules(viewer, owner, raw_data, privacy)
        assert "message" in masked
        assert "private" in masked["message"]
        assert "country" not in masked

    def test_apply_visibility_rules_hide_fields(self):
        owner = User.objects.create_user(username='owner2', email='o2@o.com', password='pwd')
        viewer = User.objects.create_user(username='viewer2', email='v2@v.com', password='pwd')
        
        privacy = UserPrivacy(user=owner, profile_visibility='PUBLIC', hide_country=True, hide_favorite_games=True)
        raw_data = {
            "country": "US", 
            "display_name": "Test",
            "favorite_games": ["game1"],
            "biography": "Hello"
        }
        
        masked = PrivacyService.apply_visibility_rules(viewer, owner, raw_data, privacy)
        assert "country" not in masked
        assert "favorite_games" not in masked
        assert "biography" in masked

    def test_apply_visibility_rules_own_profile(self):
        owner = User.objects.create_user(username='owner3', email='o3@o.com', password='pwd')
        
        privacy = UserPrivacy(user=owner, profile_visibility='PRIVATE', hide_country=True)
        raw_data = {"country": "US", "display_name": "Test"}
        
        # Viewer IS owner
        masked = PrivacyService.apply_visibility_rules(owner, owner, raw_data, privacy)
        assert "country" in masked
        assert "message" not in masked
