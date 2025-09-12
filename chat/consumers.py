import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

        self.send(text_data=json.dumps({'message': f"Connected to {self.room_group_name}! Please note: this project is IN DEVELOPMENT and will have frequent changes. Messages are UNENCRYPTED. ANYONE CAN SEE YOUR MESSAGES. Currently messages are not saved anywhere. My server is easily exploitable so use at your own risk."}))
        print("connected")
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )
        print("recieved")
    def chat_message(self, event):
        message = event["message"]

        self.send(text_data=json.dumps({
            "message": message
        }))
        print("sent")