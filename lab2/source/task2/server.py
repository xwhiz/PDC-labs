import socket
import json


class Server:
    def __init__(self, port):
        self.server_address = ("0.0.0.0", port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)
        self.users = {}  # Store connected users: {user_id: (name, address)}
        self.rooms = {}  # Store rooms information.
        self.message_queue = {}  # Store messages for each user.

    def handle_client(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            try:
                message = json.loads(data.decode())
                request = message.get("request")

                if request == "register":
                    user_id = message["id"]
                    name = message["name"]
                    self.users[user_id] = (name, addr)
                    # Optionally send an acknowledgement back to the client.
                    self.sock.sendto(json.dumps({"status": "success"}).encode(), addr)

                elif request == "list-users":
                    user_list = [
                        {"id": user_id, "name": name}
                        for user_id, (name, _) in self.users.items()
                    ]
                    response = {"success": True, "message": user_list}
                    self.sock.sendto(json.dumps(response).encode(), addr)

                elif request == "send-private-message":
                    sender_id = message["id"]
                    sender_name = self.users[sender_id][0]
                    target_user_id = message["target_user_id"]
                    message_content = message["message"]

                    if target_user_id in self.users:
                        target_address = self.users[target_user_id][1]
                        response = {"user": sender_name, "message": message_content}
                        self.sock.sendto(json.dumps(response).encode(), target_address)

                        # Send the same message back to the sender for their chat window
                        self.sock.sendto(
                            json.dumps(response).encode(), self.users[sender_id][1]
                        )

                    else:
                        response = {"success": False, "message": "User not found."}
                        self.sock.sendto(json.dumps(response).encode(), addr)

                # ... (Other request handling if needed)

            except json.JSONDecodeError:
                print("Invalid JSON received.")
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    server = Server(2055)
    print("Server started. Listening for connections...")
    server.handle_client()
