import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.decorators import login_required
from .models import Room, Message
from django.core.cache import cache

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.user = self.scope["user"]
        print(self.user)
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        # theres a couple of problems to this
        # if someone leaves and joins at the same time, the redis cache gets fucked up
        # if the user has multiple connections and leaves one, they get removed from the list even if they have another active connection
        # its pretty inefficient
        if cache.has_key(self.room_group_name):
            users = cache.get(self.room_group_name)
            users.add(self.user)
            cache.set(self.room_group_name, users)
        else:
            cache.set(self.room_group_name, {self.user})
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "update.users"}
        )


        messages = Message.objects.filter(room=Room.objects.get(slug=self.room_name)).order_by('-timestamp')[:50]
        for message in reversed(messages):
            self.send(text_data=json.dumps({'type': 'message', 'user': str(message.user), 'message': str(message.content)}))
        self.send(text_data=json.dumps({'type': 'message', 'user': "[SYSTEM]", 'message': f"Welcome, {self.user}. Connected to {self.room_group_name}! "}))
        print("connected")


    def disconnect(self, close_code):
        #the chances of someone actually leaving and joining at the same time is pretty small right...
        users = cache.get(self.room_group_name)
        users.remove(self.user)
        cache.set(self.room_group_name, users)
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "update.users"}
        )


    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        #if we receive a message, send it to the group
        #these comments look like its chatgpt but its not i promise this shit is getting too complicated
        if text_data_json["type"] == "message":
            message = text_data_json["message"]
            user = self.scope["user"]

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "chat.message", "message": message, "user": self.user.username}
            )
            print("recieved")
            Message.objects.create(room=Room.objects.get(slug=self.room_name), user=user, content=message)
        # if we receive a load_messages request, send the last 50 messages to the user
        elif text_data_json["type"] == "load_messages":
            loaded = text_data_json["msgs_loaded"]
            total_messages = Message.objects.filter(room=Room.objects.get(slug=self.room_name)).count()
            if loaded >= total_messages:
                return
            messages = Message.objects.filter(room=Room.objects.get(slug=self.room_name)).order_by('-timestamp')[loaded:20+loaded]
            #not reversed bc client is prepending
            for message in messages:
                self.send(text_data=json.dumps({'type': "old_message", 'user': str(message.user), 'message': str(message.content)}))
            print("loaded")

    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps({
            "message": message,
            "user": event["user"],
            "type": "message",
        }))
        print("sent")
    def update_users(self, event):
        users = list(cache.get(self.room_group_name))
        self.send(text_data=json.dumps({'type': 'users', 'users': [str(user) for user in users]}))
        print("sent users")