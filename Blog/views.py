from django.shortcuts import render,get_object_or_404
from rest_framework.generics import CreateAPIView,ListAPIView,RetrieveAPIView,UpdateAPIView,DestroyAPIView,RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import RegisterSerializer,PostSerializer,ProfileSerializer,FollowSerializer,FollowUserSerializer,LikeUserSerializer,CommentSerializer,CommentUpdateSerializer,CommentListSerializer,ConversationSerializer,MessageSerializer
from .permissions import IsOwner,IsCommentOwner
from .models import Post,Profile,Follow,Like,Comment,Conversation,Message
from .paginations import PostPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filtering import PostFilter
from rest_framework.filters import SearchFilter
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User=get_user_model()

# Create your views here.

class RegisterView(CreateAPIView):
    serializer_class=RegisterSerializer
    permission_classes=[AllowAny]

class PostListView(ListAPIView):
    queryset=Post.objects.all().order_by('-created_at')
    serializer_class=PostSerializer
    permission_classes=[AllowAny]
    pagination_class=PostPagination
    filter_backends=[DjangoFilterBackend, SearchFilter]
    filterset_class=PostFilter
    search_fields=['title', 'content']
    

class PostCreateView(CreateAPIView):
    queryset=Post.objects.all()
    serializer_class=PostSerializer
    permission_classes=[IsAuthenticated]
 
    def perform_create(self, serializer):
        serializer.save(author=self.request.user) 

class PostRetrieveView(RetrieveAPIView):
    queryset=Post.objects.all()
    serializer_class=PostSerializer
    permission_classes=[AllowAny]

class PostUpdateView(UpdateAPIView):
    queryset=Post.objects.all()
    serializer_class=PostSerializer
    permission_classes=[IsOwner]

class PostDestroyView(DestroyAPIView):
    queryset=Post.objects.all()
    serializer_class=PostSerializer
    permission_classes=[IsOwner]

class ProfileView(RetrieveUpdateAPIView):
    serializer_class=ProfileSerializer
    permission_classes=[IsAuthenticated]

    def get_object(self):
        return self.request.user.profile

class OtherProfileView(RetrieveAPIView):
    serializer_class=ProfileSerializer
    permission_classes=[AllowAny]

    def get_object(self):
        username=self.kwargs['username']
        return get_object_or_404(Profile, user__username=username)

class FollowView(CreateAPIView):
    serializer_class=FollowSerializer
    permission_classes=[IsAuthenticated]

    def create(self, request, *args, **kwargs):
        target_user=get_object_or_404(User,username=kwargs['username'])

        if target_user==request.user:
            return Response({"detail":"You cannot follow yourself."},status=status.HTTP_400_BAD_REQUEST)

        if Follow.objects.filter(follower=request.user,following=target_user).exists():
            return Response({"detail":"You are already following this user."},status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(follower=request.user,following=target_user)
        return Response({"detail":"Followed successfully."},status=status.HTTP_201_CREATED)

class UnfollowView(DestroyAPIView):
    permission_classes=[IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        target_user=get_object_or_404(User,username=kwargs['username'])
        follow=Follow.objects.filter(follower=request.user,following=target_user).first()

        if target_user==request.user:
            return Response({"detail":"You cannot unfollow yourself."},status=status.HTTP_400_BAD_REQUEST)

        if not follow:
            return Response({"detail":"You are not following this user."},status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response({"detail":"Unfollowed successfully."},status=status.HTTP_201_CREATED)

class FollowStatusView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request, *args, **kwargs):
        target_user=get_object_or_404(User,username=kwargs['username'])
        is_following=Follow.objects.filter(follower=request.user,following=target_user).exists()
        follows_me=Follow.objects.filter(follower=target_user,following=request.user).exists()

        return Response({
            "username":target_user.username,
            "is_following":is_following,
            "follows_me":follows_me
        })

class FollowersListView(ListAPIView):
    serializer_class = FollowUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        target_user = get_object_or_404(
            User,
            username=self.kwargs['username']
        )

        if self.request.user != target_user:
            is_mutual = (
                Follow.objects.filter(
                    follower=self.request.user,
                    following=target_user
                ).exists()
                and
                Follow.objects.filter(
                    follower=target_user,
                    following=self.request.user
                ).exists()
            )

            if not is_mutual:
                raise PermissionDenied(
                    "You can only see this user's followers if you follow each other."
                )

        return User.objects.filter(
            followings__following=target_user
        )

class FollowingListView(ListAPIView):
    serializer_class = FollowUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        target_user = get_object_or_404(
            User,
            username=self.kwargs['username']
        )

        if self.request.user != target_user:
            is_mutual = (
                Follow.objects.filter(
                    follower=self.request.user,
                    following=target_user
                ).exists()
                and
                Follow.objects.filter(
                    follower=target_user,
                    following=self.request.user
                ).exists()
            )

            if not is_mutual:
                raise PermissionDenied(
                    "You can only see this user's following if you follow each other."
                )

        return User.objects.filter(
            followers__follower=target_user
        )

class FeedView(ListAPIView):
    serializer_class=PostSerializer
    permission_classes=[IsAuthenticated]
    pagination_class=PostPagination

    def get_queryset(self):
        following_users=self.request.user.followings.values_list('following_id',flat=True)
        return Post.objects.filter(Q(author=self.request.user)|Q(author_id__in=following_users)).order_by('-created_at')       

class LikeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user,post=post)

        if not created:
            return Response(
                {"detail": "You already liked this post."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "Post liked successfully."},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        like = Like.objects.filter(user=request.user,post=post).first()

        if not like:
            return Response(
                {"detail": "You have not liked this post."},
                status=status.HTTP_400_BAD_REQUEST
            )

        like.delete()

        return Response(
            {"detail": "Post unliked successfully."},
            status=status.HTTP_200_OK
        )

class LikeListView(ListAPIView):
    serializer_class=LikeUserSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        post_id=self.kwargs['pk']
        return User.objects.filter(likes__post_id=post_id)

class CommentCreateView(CreateAPIView):
    serializer_class=CommentSerializer
    permission_classes=[IsAuthenticated]

    def perform_create(self, serializer):
        post=get_object_or_404(Post,pk=self.kwargs['pk'])
        serializer.save(user=self.request.user,post=post)

class CommentUpdateView(UpdateAPIView):
    serializer_class=CommentUpdateSerializer
    permission_classes=[IsAuthenticated,IsCommentOwner]

    def get_queryset(self):
        return Comment.objects.all()

class CommentDeleteView(DestroyAPIView):
    queryset=Comment.objects.all()
    permission_classes=[IsAuthenticated,IsCommentOwner]

class CommentListView(ListAPIView):
    serializer_class=CommentListSerializer
    permission_classes=[AllowAny]

    def get_queryset(self):
        post=get_object_or_404(Post,pk=self.kwargs['pk'])
        return Comment.objects.filter(post=post,parent__isnull=True).prefetch_related('replies').order_by('-created_at')

class ConversationCreateView(CreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user1 = request.user
        user2 = get_object_or_404(User, pk=self.kwargs["pk"])

        if user1 == user2:
            return Response(
                {"error": "You cannot chat with yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation = Conversation.objects.filter(
            Q(user1=user1, user2=user2) |
            Q(user1=user2, user2=user1)
        ).first()

        if conversation:
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)

        conversation = Conversation.objects.create(
            user1=user1,
            user2=user2
        )

        serializer = self.get_serializer(conversation)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

class ConversationListView(ListAPIView):
    serializer_class=ConversationSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        user=self.request.user
        return Conversation.objects.filter(Q(user1=user) | Q(user2=user)).order_by('-created_at')

class MessageListView(ListAPIView):
    serializer_class=MessageSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        conversation=get_object_or_404(Conversation.objects.filter(Q(user1=self.request.user) | Q(user2=self.request.user)),
        pk=self.kwargs["pk"]                               
        )

        return Message.objects.filter(conversation=conversation).order_by("created_at")

class MessageReadView(APIView):
    permission_classes=[IsAuthenticated]
    
    def patch(self, request, conversation_id, message_id):
        conversation=get_object_or_404(Conversation.objects.filter(Q(user1=request.user)|Q(user2=request.user)),pk=conversation_id)

        message=get_object_or_404(Message,pk=message_id,conversation=conversation)

        if message.is_read==True:
            return Response({"error":"Message is already marked as read."},status=status.HTTP_400_BAD_REQUEST)

        if message.sender==request.user:
            return Response({"error":"You cannot mark your own message as read."},status=status.HTTP_400_BAD_REQUEST)

        message.is_read=True
        message.save(update_fields=["is_read"])

        channel_layer=get_channel_layer()
        async_to_sync(channel_layer.group_send)(f"chat_{conversation_id}",{
            "type":"message_read",
            "message_id":message_id,
            "read_by":request.user.username
        })

        return Response({"message":"Message marked as read."},status=status.HTTP_200_OK)

             

    


     




    

    

        





    

           




