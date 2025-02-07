import socket
from chatroom import ChatRoom
import json
from uuid import uuid4
import time

from user import User


def generate_unique_id() -> str:
    return str(uuid4()).split("-")[1]


class ChatServer:
    def __init__(self, ip: str = "127.0.0.1", port: int = 2055):
        print("Initializing server")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))
        print(f"Server Listening on {ip}:{port}")

        self.rooms: list[ChatRoom] = []

    def listen(self):
        print("Listening to receive messages")
        while True:
            message, address = self.socket.recvfrom(1024)
            message = message.decode()
            body = json.loads(message)
            print(f"Received from {address=} {body=}")

            request_type = body.get("request")

            if not request_type:
                self.socket.sendto(
                    json.dumps({"success": False, "message": "Invalid request"})
                )
                continue

            if request_type == "create-room":
                self.create_room(body, address)
            elif request_type == "send-message":
                self.send_message(body)
                pass
            else:
                pass

        self.socket.close()

    def create_room(self, body: dict, address):
        user = User(
            id=body.get("user_id"),
            name=body.get("user_name"),
            address=address,
        )
        room_id = generate_unique_id()
        self.socket.sendto(
            json.dumps(
                {
                    "success": True,
                    "message": "Room created successfully",
                    "room_id": room_id,
                }
            ).encode(),
            address,
        )
        room_name: str = body.get("room_name") or generate_unique_id()
        room = ChatRoom(room_id, room_name, self.socket)
        self.rooms.append(room)
        room.add_user(user)


if __name__ == "__main__":
    server = ChatServer()
    server.listen()
