import pytest
from django.contrib.auth import get_user_model
from apps.friends.services import FriendRequestService, FriendService, BlockService
from apps.friends.selectors import FriendSelector, BlockSelector
from apps.friends.models import FriendRequest

User = get_user_model()

@pytest.mark.django_db
class TestFriendServices:
    def setup_method(self):
        self.user1 = User.objects.create_user(username='u1', email='1@example.com', password='pwd')
        self.user2 = User.objects.create_user(username='u2', email='2@example.com', password='pwd')
        self.user3 = User.objects.create_user(username='u3', email='3@example.com', password='pwd')

    def test_send_request_success(self):
        success, msg = FriendRequestService.send_request(self.user1, self.user2)
        assert success
        req = FriendSelector.get_request(self.user1, self.user2)
        assert req.status == FriendRequest.Status.PENDING

    def test_send_request_blocked(self):
        # User2 blocks User1
        BlockService.block_user(self.user2, self.user1)
        
        # User1 tries to send request to User2
        success, msg = FriendRequestService.send_request(self.user1, self.user2)
        assert not success
        assert "Cannot send friend request" in msg

    def test_accept_request(self):
        FriendRequestService.send_request(self.user1, self.user2)
        success, msg = FriendRequestService.accept_request(self.user1, self.user2)
        
        assert success
        assert FriendSelector.is_friend(self.user1, self.user2)

    def test_block_destroys_friendship(self):
        # Become friends
        FriendRequestService.send_request(self.user1, self.user2)
        FriendRequestService.accept_request(self.user1, self.user2)
        assert FriendSelector.is_friend(self.user1, self.user2)
        
        # User1 blocks User2
        success, msg = BlockService.block_user(self.user1, self.user2)
        assert success
        
        # Verify friendship is destroyed
        assert not FriendSelector.is_friend(self.user1, self.user2)
        assert BlockSelector.is_blocked(self.user1, self.user2)
