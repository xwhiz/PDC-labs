import socket
from chatroom import ChatRoom
import json
from uuid import uuid4

def generate_unique_id() -> str:
    return str(uuid4()).split('-')[1]


class ChatServer:
    def __init__(self, ip: str = "127.0.0.1", port: int = 2055):
        print("Initializing server")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((ip, port))
        print(f"Server Listening on {ip}:{port}")

        self.rooms: list[ChatRoom] = []

    def listen(self):
        print("Listening to receive messages")
        while True:
            message, address = self.server.recvfrom(1024)
            message = message.decode()
            body = json.dumps(message)
            print(f"Received from {address=} {body=}")

            request_type = body.get("request")

            if not request_type:
                self.server.sendto(
                    json.dumps({"success": False, "message": "Invalid request"})
                )
                continue
            
            if request_type == "create-room":
                room_id = generate_unique_id()
                room = ChatRoom(room_id, body.get("name"))
                
            elif request_type == "":
                pass
            else:
                

            self.server.sendto("Received".encode(), address)

        self.server.close()
        
    def create_room(self, name: str, user_id: str)


if __name__ == "__main__":
    server = ChatServer()
    server.listen()
