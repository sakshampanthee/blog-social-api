from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class User(AbstractUser):
    pass

class Post(models.Model):
    title=models.CharField(max_length=200)
    content=models.TextField()
    image=models.ImageField(upload_to='posts/',blank=True,null=True)
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='posts')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title 

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    bio=models.TextField(blank=True)
    profile_image=models.ImageField(upload_to='profiles/',blank=True,null=True)

    def __str__(self):
        return self.user.username

class Follow(models.Model):
    follower=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='followings')
    following=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='followers')
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints=[
            models.UniqueConstraint(
                fields=['follower','following'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            ),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class Like(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='likes')
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='likes')
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints=[
            models.UniqueConstraint(
                fields=['user','post'],
                name='unique_user_post_like'
            ),
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"

class Comment(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='comments')
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    parent=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='replies')
    content=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.post.title} -{self.content[:30]}"

class Conversation(models.Model):
    user1=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='conversations_as_user1')            
    user2=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='conversations_as_user2')
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user1.username} - {self.user2.username}"

class Message(models.Model):
    conversation=models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name='messages')
    sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='sent_messages')
    content=models.TextField()
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"                    
    
