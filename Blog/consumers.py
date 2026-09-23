from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.db.models import Q
from .models import Conversation,Message
from channels.db import database_sync_to_async
import json
import redis

class ChatConsumer(WebsocketConsumer):

    @property
    def redis_client(self):
      return redis.Redis(
        host="127.0.0.1",
        port=6379,
        decode_responses=True
    )

    @database_sync_to_async
    def save_message(self, content):
      return Message.objects.create(
        conversation_id=self.conversation_id,
        sender=self.scope["user"],
        content=content
    )

    def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        user=self.scope["user"]
        
        conversation=Conversation.objects.filter(Q(id=self.conversation_id)&(Q(user1=user)|Q(user2=user))).first()

        if not conversation:
            self.close()
            return

        self.group_name=f"chat_{self.conversation_id}"

        async_to_sync(self.channel_layer.group_add)(self.group_name,self.channel_name)

        redis_client = self.redis_client
        presence_key = f"presence:{self.conversation_id}:{user.id}"
        connection_count_before = redis_client.scard(presence_key)

        redis_client.sadd(
           presence_key,
           self.channel_name
        )

        if connection_count_before == 0:
            async_to_sync(
               self.channel_layer.group_send
            )(
               self.group_name,
            {
            "type": "user_status",
            "username": user.username,
            "is_online": True
            }) 

        print("USER:", user)
        print("CONVERSATION", conversation.id)
        print("GROUP:", self.group_name)

        self.accept()

    def receive(self,text_data):
        data = json.loads(text_data)

        if data.get("type") == "typing":
            async_to_sync(self.channel_layer.group_send)(self.group_name,
            {
                "type": "typing_status",
                "username": self.scope["user"].username,
                "is_typing": data.get("is_typing", False)
            })
            return
        
        message=async_to_sync(self.save_message)(text_data)

        message_data = {
        "id": message.id,
        "conversation":message.conversation_id,
        "sender": message.sender.username,
        "content": message.content,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat(),
    }

        async_to_sync(self.channel_layer.group_send)(self.group_name,{"type": "chat_message", "message": message_data})

    def chat_message(self, event):
        print("EVENT:", event)

        self.send(text_data=json.dumps(event["message"]))

    def message_read(self, event):
        self.send(text_data=json.dumps({
            "type": "message_read",
            "message_id": event["message_id"],
            "read_by": event["read_by"]
        }))

    def typing_status(self, event):
        self.send(text_data=json.dumps({
            "type": "typing",
            "username": event["username"],
            "is_typing": event["is_typing"]
        }))

    def user_status(self, event):
        self.send(text_data=json.dumps({
        "username": event["username"],
        "is_online": event["is_online"]
    }))            

    def disconnect(self, close_code):
        redis_client = self.redis_client
        presence_key = f"presence:{self.conversation_id}:{self.scope['user'].id}"

        redis_client.srem(
           presence_key,
           self.channel_name
        )

        remaining_connections = redis_client.scard(presence_key)

        if remaining_connections == 0:
            redis_client.delete(presence_key)

            async_to_sync(
               self.channel_layer.group_send
            )(
               self.group_name,
               {
                   "type": "user_status",
                   "username": self.scope["user"].username,
                   "is_online": False
                }
            )

        async_to_sync(self.channel_layer.group_discard)(self.group_name,self.channel_name)
        
        
               

                    