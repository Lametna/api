from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema

from .serializers import CommunitySerializer, CommunityPostSerializer, CommunityCreateSerializer, CommunityJoinSerializer, PostCreateSerializer, PolymorphicFeedSerializer
from .services import CommunityService, MembershipService, PostService
from .selectors import CommunitySelector, PostSelector, FeedSelector

class CommunityListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CommunitySerializer(many=True)})
    def get(self, request):
        query = request.query_params.get('q', '')
        if query:
            comms = CommunitySelector.search_communities(query)
        else:
            comms = CommunitySelector.get_trending_communities()
        return Response({"success": True, "data": CommunitySerializer(comms, many=True).data})

    @extend_schema(request=CommunityCreateSerializer, responses={201: CommunitySerializer})
    def post(self, request):
        serializer = CommunityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, comm, msg = CommunityService.create_community(
            request.user, 
            serializer.validated_data['name'], 
            serializer.validated_data['privacy'],
            description=serializer.validated_data.get('description', '')
        )
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "data": CommunitySerializer(comm).data}, status=status.HTTP_201_CREATED)

class CommunityDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CommunitySerializer})
    def get(self, request, pk):
        comm = CommunitySelector.get_community(pk)
        if not comm:
            return Response({"success": False, "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"success": True, "data": CommunitySerializer(comm).data})

class CommunityJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=CommunityJoinSerializer)
    def post(self, request, pk):
        serializer = CommunityJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, msg = MembershipService.join_community(request.user, pk, serializer.validated_data.get('password'))
        return Response({"success": success, "message": msg}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)

class CommunityPostListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: CommunityPostSerializer(many=True)})
    def get(self, request, pk):
        comm = CommunitySelector.get_community(pk)
        if not comm:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
        posts = PostSelector.get_posts(comm)
        return Response({"success": True, "data": CommunityPostSerializer(posts, many=True).data})

    @extend_schema(request=PostCreateSerializer)
    def post(self, request, pk):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        success, post, msg = PostService.create_post(
            request.user, pk, serializer.validated_data['content'], serializer.validated_data['type']
        )
        if not success:
            return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": True, "data": CommunityPostSerializer(post).data}, status=status.HTTP_201_CREATED)

class CommunityFeedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: PolymorphicFeedSerializer(many=True)})
    def get(self, request, pk):
        comm = CommunitySelector.get_community(pk)
        if not comm:
            return Response({"success": False}, status=status.HTTP_404_NOT_FOUND)
            
        feed_items = FeedSelector.get_unified_feed(comm)
        return Response({
            "success": True, 
            "data": PolymorphicFeedSerializer(feed_items, many=True).data
        })
