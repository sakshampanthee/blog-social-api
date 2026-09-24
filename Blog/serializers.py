from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post,Profile,Follow,Like,Comment,Conversation,Message

User= get_user_model() 

class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    password2=serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields=["username","email","password","password2"]

    def validate(self, attrs):
        if attrs["password"]!=attrs["password2"]:
            raise serializers.ValidationError({"password":"Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")

        user=User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        ) 
        return user 

class PostSerializer(serializers.ModelSerializer):
    profile_image=serializers.ImageField(source='author.profile.profile_image',read_only=True)
    author=serializers.ReadOnlyField(source='author.username')
    like_count=serializers.SerializerMethodField()
    is_liked=serializers.SerializerMethodField()
    comment_count=serializers.SerializerMethodField()

    class Meta:
        model=Post
        fields=['id','title','content','profile_image','image','author','like_count','is_liked','comment_count','created_at','updated_at']
        read_only_fields=['id','created_at','updated_at']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request=self.context['request']

        if request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()

        return False

    def get_comment_count(self, obj):
        return obj.comments.count()

class ProfileSerializer(serializers.ModelSerializer):
    username=serializers.CharField(source='user.username',read_only=True)
    followers_count=serializers.SerializerMethodField()
    following_count=serializers.SerializerMethodField()

    class Meta:
        model=Profile
        fields=['username','bio','profile_image','followers_count','following_count']

    def get_followers_count(self, obj):
        return obj.user.followers.count()
       
    def get_following_count(self, obj):
        return obj.user.followings.count()    

class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model=Follow
        fields=['id','follower','following','created_at']
        read_only_fields=['id','follower','following','created_at']

class FollowUserSerializer(serializers.ModelSerializer):
    profile_image=serializers.ImageField(source='profile.profile_image',read_only=True)

    class Meta:
        model=User
        fields=['profile_image','username']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model=Like
        fields=['id','user','post','created_at']
        read_only_fields=['id','user','post','created_at']

class LikeUserSerializer(serializers.ModelSerializer):
    profile_image=serializers.ImageField(source='profile.profile_image',read_only=True)

    class Meta:
        model=User
        fields=['profile_image','username'] 

class CommentSerializer(serializers.ModelSerializer):
    username=serializers.ReadOnlyField(source='user.username')
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(),allow_null=True,required=False)

    class Meta:
        model=Comment
        fields=['id','username','post','parent','content','created_at','updated_at']
        read_only_fields=['id','username','post','created_at','updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        view = self.context.get('view')

        if view:
            post_id = view.kwargs.get('pk')
            if post_id:
                self.fields['parent'].queryset = Comment.objects.filter(post_id=post_id)    

    def validate(self, attrs):
        parent=attrs.get('parent')
        post=self.context['view'].kwargs['pk']

        if parent:
            if parent.post_id!=int(post):
                raise serializers.ValidationError({"parent":"You can only reply to a comment on this post"})
        return attrs

class CommentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['content']

class CommentListSerializer(serializers.ModelSerializer):
    username=serializers.ReadOnlyField(source='user.username')
    profile_image=serializers.ImageField(source='user.profile.profile_image',read_only=True)
    replies=serializers.SerializerMethodField()

    class Meta:
        model=Comment
        fields=['id','profile_image','username','content','created_at','updated_at','replies']

    def get_replies(self, obj):
        replies=obj.replies.all().order_by('-created_at')
        return CommentListSerializer(replies,many=True,context=self.context).data

class ConversationSerializer(serializers.ModelSerializer):
    user1 = serializers.CharField(source="user1.username", read_only=True)
    user1_profile_image=serializers.ImageField(source='user1.profile.profile_image',read_only=True)
    user2 = serializers.CharField(source="user2.username", read_only=True)
    user2_profile_image=serializers.ImageField(source='user2.profile.profile_image',read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "user1","user1_profile_image","user2","user2_profile_image", "created_at"]

class MessageSerializer(serializers.ModelSerializer):
    profile_image=serializers.ImageField(source='sender.profile.profile_image',read_only=True)
    sender = serializers.CharField(source="sender.username",read_only=True)

    class Meta:
        model = Message
        fields = ["id","conversation","profile_image","sender","content","is_read","created_at"]


    



    


                        
