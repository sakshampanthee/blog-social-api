from django.contrib import admin
from .models import User,Post,Profile,Follow,Like,Comment,Conversation,Message

# Register your models here.

admin.site.register(User)
admin.site.register(Post)
admin.site.register(Profile)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Conversation)
admin.site.register(Message)