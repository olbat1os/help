import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth.models import User
from .serializers import MessageSerializer
from django.shortcuts import get_object_or_404

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
     self.chat_id = self.scope['url_route']['kwargs']['chat_id']
     self.room_group_name = f"chat_{self.chat_id}"

     try:
        chat = await self.get_chat_from_db()
        user = self.scope['user']
        if user not in chat.participants.all():
            await self.close(code=4004) # Unauthorized
            print(f"Connection closed. User {user} not in chat {self.chat_id}")
            return
     except Exception as e:
         print(f"Connection closed. Error: {e}")
         await self.close(code=4005) # Error
         return

     await self.channel_layer.group_add(self.room_group_name, self.channel_name)
     await self.accept()
     print(f"User: {self.scope['user']}, Connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        user = self.scope['user']
        try:
            message_obj = await self.create_message_in_db(message, user)
            message_json = MessageSerializer(message_obj).data
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat.message", "message": message_json}
            )
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_chat_from_db(self):
        return get_object_or_404(Chat, id=self.chat_id)

    @database_sync_to_async
    def create_message_in_db(self, message, user):
        chat = get_object_or_404(Chat, id=self.chat_id)
        message_obj = Message.objects.create(sender=user, chat=chat, text=message)
        return message_obj
