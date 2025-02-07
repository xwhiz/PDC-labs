import socket
from user import User
import json


class ChatRoom:
    def __init__(self, room_id: str, name: str, server_socket: socket.socket):
        self.room_id = room_id
        self.name = name
        self.socket = server_socket
        self.users: list[User] = []

    def add_user(self, user: User):
        self.users.append(user)
        self.publish({"user": self.name, "message": f"{user.name} joined the room."})

    def remove_user(self, user_id: str):
        cur_user = self.users[0]
        for user in self.users:
            if user.id == user_id:
                user = cur_user
                break

        self.users.remove(user)
        self.publish({"user": self.name, "message": f"{user.name} left the room."})

    def publish(self, payload: dict):
        for user in self.users:
            self.socket.sendto(json.dumps(payload).encode(), user.address)
