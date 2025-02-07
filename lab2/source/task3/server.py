import socket
import json
import os
import threading


class Server:
    def __init__(self, port):
        self.server_address = ("0.0.0.0", port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)
        self.users = {}
        self.file_requests = {}

    def handle_client(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
            try:
                message = json.loads(data.decode())
                request = message.get("request")

                if request == "register":
                    user_id = message["id"]
                    name = message["name"]
                    self.users[user_id] = (name, addr)
                    self.sock.sendto(json.dumps({"status": "success"}).encode(), addr)

                elif request == "list-users":
                    user_list = [
                        {"id": user_id, "name": name}
                        for user_id, (name, _) in self.users.items()
                    ]
                    self.sock.sendto(
                        json.dumps({"success": True, "message": user_list}).encode(),
                        addr,
                    )

                elif request == "send-file":
                    target_user_id = message["target_user_id"]
                    if target_user_id in self.users:
                        self.sock.sendto(
                            json.dumps(message).encode(), self.users[target_user_id][1]
                        )

                elif request == "file-chunk":
                    target_user_id = message["target_user_id"]
                    if target_user_id in self.users:
                        self.sock.sendto(
                            json.dumps(message).encode(), self.users[target_user_id][1]
                        )

                elif request == "request-file":
                    target_user_id = message["target_user_id"]
                    if target_user_id in self.users:
                        self.sock.sendto(
                            json.dumps(message).encode(), self.users[target_user_id][1]
                        )

                elif request == "approve-file-request":
                    sender_id = message["sender_id"]
                    filename = message["filename"]
                    if sender_id in self.users:
                        response = {
                            "request": "file-request-approved",
                            "filename": filename,
                        }
                        self.sock.sendto(
                            json.dumps(response).encode(), self.users[sender_id][1]
                        )

            except json.JSONDecodeError:
                print("Invalid JSON received.")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    server = Server(2055)
    print("Server started. Listening for connections...")
    server.handle_client()
