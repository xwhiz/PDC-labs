import socket
import json
from uuid import uuid4
import threading as th


class User:
    server_address = ("0.0.0.0", 2055)

    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        self.con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.register()

    def reinit_connection(self):
        self.con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.register()

    def register(self):
        body = {"name": self.name, "id": self.id, "request": "register"}
        self.con.sendto(json.dumps(body).encode(), User.server_address)
        data, _ = self.con.recvfrom(1024)  # Acknowledge from server (optional)

    def request_for_user_list(self):
        body = {"name": self.name, "id": self.id, "request": "list-users"}
        self.con.sendto(json.dumps(body).encode(), User.server_address)

        data, _ = self.con.recvfrom(1024)
        response = json.loads(data.decode())

        if response.get("success"):
            print("%-6s\t%s" % ("ID", "User Name"))
            for user in response.get("message", []):
                print(f"{user['id']}\t{user['name']}")

    def send_private_message(self, target_user_id: str, message: str):
        body = {
            "user_name": self.name,
            "id": self.id,
            "request": "send-private-message",
            "target_user_id": target_user_id,
            "message": message,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

    def log_messages(self, stop_event: th.Event):
        print("Logging messages...")

        while True:
            if stop_event.is_set():
                return

            try:
                data, _ = self.con.recvfrom(1024)
                response = json.loads(data.decode())
                print(f"\r[{response['user']}]: {response['message']}\n> ", end="")
            except OSError:
                pass


if __name__ == "__main__":
    name = input("Enter your name: ")
    user_id = str(uuid4()).split("-")[1]
    user = User(name, user_id)
    joined_user_id = None
    is_chatting = False
    update_thread = None
    stop_event = th.Event()

    while True:
        if not is_chatting:
            print("""\nPlease select one of the option:
    1. List users
    2. Chat with user
    q. Exit""")
            choice = input("> ").lower()
            if choice == "q":
                print("Quitting the application...")
                exit()
            elif choice == "1":
                user.request_for_user_list()
            elif choice == "2":
                user.request_for_user_list()
                joined_user_id = input(
                    "The user id you want to chat with: "
                )  # Directly get user ID

                is_chatting = True
                stop_event.clear()
                update_thread = th.Thread(target=user.log_messages, args=(stop_event,))
                update_thread.start()
            else:
                print("Please select one of the options only.")

        else:
            message = input("> ")
            if message == "exit":
                print("Leaving the chat...")
                joined_user_id = None
                is_chatting = False
                stop_event.set()
                user.con.close()
                update_thread.join()  # type: ignore
                print("\nYou left the chat")
                user.reinit_connection()
                continue

            user.send_private_message(joined_user_id or "", message)
