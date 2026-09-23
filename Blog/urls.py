from django.urls import path
from .views import RegisterView,PostListView,PostCreateView,PostRetrieveView,PostUpdateView,PostDestroyView,ProfileView,OtherProfileView,FollowView,UnfollowView,FollowStatusView,FollowersListView,FollowingListView,FeedView,LikeView,LikeListView,CommentCreateView,CommentUpdateView,CommentDeleteView,CommentListView,ConversationCreateView,ConversationListView,MessageListView,MessageReadView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/create/', PostCreateView.as_view(), name='post-create'),
    path('posts/<int:pk>/', PostRetrieveView.as_view(), name='post-detail'),
    path('posts/update/<int:pk>/', PostUpdateView.as_view(), name='post-update'),
    path('posts/delete/<int:pk>/', PostDestroyView.as_view(), name='post-delete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('<str:username>/profile/', OtherProfileView.as_view(), name='other-profile'),
    path('<str:username>/follow/', FollowView.as_view(), name='follow'),
    path('<str:username>/unfollow/', UnfollowView.as_view(), name='unfollow'), 
    path('<str:username>/follow-status/', FollowStatusView.as_view(), name='follow-status'),
    path('<str:username>/followers/', FollowersListView.as_view(), name='followers'),
    path('<str:username>/following/', FollowingListView.as_view(), name='following'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('posts/<int:pk>/like/', LikeView.as_view(), name='post-like'),
    path('posts/<int:pk>/likes/', LikeListView.as_view(), name='like-list'),
    path('posts/<int:pk>/comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('comments/<int:pk>/update/', CommentUpdateView.as_view(), name='comment-update'),
    path('comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
    path('posts/<int:pk>/commentslist/', CommentListView.as_view(), name='comment-list'),
    path('conversations/<int:pk>/create/', ConversationCreateView.as_view(),name="conversation-create"),
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path('conversations/<int:pk>/messages/', MessageListView.as_view(), name='message-list'),
    path('conversations/<int:conversation_id>/messages/<int:message_id>/read/', MessageReadView. as_view(), name='message-read'),   
]