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

    def reinit_connection(self):
        self.con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def request_to_create_room(self, room_name: str) -> str:
        body = {
            "user_name": self.name,
            "user_id": self.id,
            "request": "create-room",
            "room_name": room_name,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

        data, _ = self.con.recvfrom(1024)
        response = json.loads(data.decode())

        if response.get("success", None):
            return response.get("room_id")

        return ""

    def subscribe(self, room_id: str):
        body = {
            "name": self.name,
            "id": self.id,
            "request": "subscribe",
            "room_id": room_id,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

    def unsubscribe(self, room_id: str):
        body = {
            "name": self.name,
            "id": self.id,
            "request": "unsubscribe",
            "room_id": room_id,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

    def send_to_room(self, room_id: str, message: str):
        body = {
            "user_name": self.name,
            "id": self.id,
            "request": "send-message",
            "room_id": room_id,
            "message": message,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

    def request_for_user_list(self):
        body = {"name": self.name, "id": self.id, "request": "list-rooms"}
        self.con.sendto(json.dumps(body).encode(), User.server_address)

        data, _ = self.con.recvfrom(1024)
        response = json.loads(data.decode())

        if response.get("success"):
            print("%-6s\t%s" % ("ID", "Room Name"))
            print(response.get("message"))

    def user_exists(self, room_id: str) -> bool:
        body = {
            "name": self.name,
            "id": self.id,
            "request": "room-exists",
            "room_id": room_id,
        }
        self.con.sendto(json.dumps(body).encode(), User.server_address)

        data, _ = self.con.recvfrom(1024)
        response = json.loads(data.decode())

        if response.get("success"):
            return response.get("exists")

        return False

    def log_messages(self, room_id: int, stop_event: th.Event):
        print("Logging messages...")

        while True:
            if stop_event.is_set():
                return

            try:
                data, _ = self.con.recvfrom(1024)
                response = json.loads(data)
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
            print(
                """\nPlease select one of the option:
    1. List users
    2. Chat with user
    q. Exit"""
            )
            choice = input("> ").lower()
            if choice == "q":
                print("Quitting the application...")
                exit()
            if choice == "1":
                user.request_for_user_list()
            elif choice == "2":
                user.request_for_user_list()
                user_id = input("The user id you want to chat with: ")

                if not user.user_exists(user_id):
                    print("Please enter a valid user id.")
                    continue

                user.subscribe(user_id)
                joined_user_id = user_id
                is_chatting = True
                stop_event.clear()
                update_thread = th.Thread(
                    target=(user.log_messages), args=(user_id, stop_event)
                )
                update_thread.start()
            else:
                print("Please select one of the options only.")
                continue
        else:
            message = input("> ")
            if message == "exit":
                print("Leaving the chat...")
                user.unsubscribe(joined_user_id or "")
                joined_user_id = None
                is_chatting = False
                stop_event.set()
                user.con.close()
                update_thread.join()  # type: ignore
                print("\nYou left the chat")
                user.reinit_connection()
                continue

            user.send_to_room(joined_user_id or "", message)
