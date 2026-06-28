from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from .serializers import ConversationSerializer, MessageSerializer, SendMessageSerializer, ConversationCreateSerializer
from .services import ConversationService, MessageService, ReceiptService, TypingService
from .selectors import ConversationSelector, MessageSelector

User = get_user_model()

class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: ConversationSerializer(many=True)})
    def get(self, request):
        convs = ConversationSelector.get_user_conversations(request.user)
        serializer = ConversationSerializer(convs, many=True, context={'request': request})
        return Response({"success": True, "data": serializer.data})

    @extend_schema(request=ConversationCreateSerializer, responses={201: ConversationSerializer})
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target = User.objects.filter(id=serializer.validated_data['target_user_id']).first()
        if not target:
            return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        success, conv, msg = ConversationService.get_or_create_direct_conversation(request.user, target)
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"success": True, "data": ConversationSerializer(conv, context={'request': request}).data})

class MessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MessageSerializer(many=True)})
    def get(self, request, conversation_id):
        conv = ConversationSelector.get_user_conversations(request.user) # Ensures member check
        conv_instance = next((c for c in conv if str(c.id) == str(conversation_id)), None)
        
        if not conv_instance:
            return Response({"success": False, "message": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
            
        msgs = MessageSelector.get_conversation_messages(conv_instance)
        return Response({"success": True, "data": MessageSerializer(msgs, many=True).data})

    @extend_schema(request=SendMessageSerializer, responses={201: MessageSerializer})
    def post(self, request, conversation_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, msg_instance, err = MessageService.send_message(
            request.user, conversation_id, 
            serializer.validated_data['content'], 
            serializer.validated_data.get('content_type', 'TEXT')
        )
        if not success:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"success": True, "data": MessageSerializer(msg_instance).data})

class MessageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=SendMessageSerializer)
    def patch(self, request, message_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, err = MessageService.edit_message(request.user, message_id, serializer.validated_data['content'])
        return Response({"success": success, "message": err}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

    def delete(self, request, message_id):
        success, err = MessageService.delete_message(request.user, message_id)
        return Response({"success": success, "message": err}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class MessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, message_id):
        success, err = ReceiptService.mark_message_read(request.user, message_id)
        return Response({"success": success, "message": err}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class TypingIndicatorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        # Fallback HTTP typing indicator. Best practice is via WebSocket.
        TypingService.start_typing(request.user, conversation_id)
        return Response({"success": True})
