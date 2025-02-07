import socket
import random
import json
import threading as th


class Client:
    server_address = ("127.0.0.1", 2055)

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
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

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
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

    def unsubscribe(self, room_id: str):
        body = {
            "name": self.name,
            "id": self.id,
            "request": "unsubscribe",
            "room_id": room_id,
        }
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

    def send_to_room(self, room_id: str, message: str):
        body = {
            "user_name": self.name,
            "id": self.id,
            "request": "send-message",
            "room_id": room_id,
            "message": message,
        }
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

        # data, _ = self.con.recvfrom(1024)
        # response = json.loads(data.decode())

        # if response.get("success"):
        #     print(response.get("message"))

    def list_chat_rooms(self):
        body = {"name": self.name, "id": self.id, "request": "list-rooms"}
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

        data, _ = self.con.recvfrom(1024)
        response = json.loads(data.decode())

        if response.get("success"):
            print("%-6s\t%s" % ("ID", "Room Name"))
            print(response.get("message"))

    def room_exists(self, room_id: str) -> bool:
        body = {
            "name": self.name,
            "id": self.id,
            "request": "room-exists",
            "room_id": room_id,
        }
        self.con.sendto(json.dumps(body).encode(), Client.server_address)

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
    name = "Hamza"
    user_id = str(random.randint(0, 10))
    client = Client(name, user_id)
    joined_room_id = None
    is_chatting = False
    update_thread = None
    stop_event = th.Event()

    while True:
        if not is_chatting:
            print(
                """\nPlease select one of the option:
    1. Create a chatroom
    2. List Chatrooms
    3. Join a chatroom"""
            )
            choice = input("> ")
            if choice == "1":
                room_name = input("Enter room name: ")
                room_id = client.request_to_create_room(room_name)

                if room_id is None:
                    print(
                        "\nUnable to create room at the moment. Please try again later.\n"
                    )
                    continue

                is_chatting = True
                joined_room_id = room_id
                stop_event.clear()
                update_thread = th.Thread(
                    target=(client.log_messages), args=(joined_room_id, stop_event)
                )
                update_thread.start()
            elif choice == "2":
                client.list_chat_rooms()
            elif choice == "3":
                client.list_chat_rooms()
                room_id = input("Please enter the room id that you want to join: ")

                if not client.room_exists(room_id):
                    print("Please enter a valid room id.")
                    continue

                client.subscribe(room_id)
                joined_room_id = room_id
                is_chatting = True
                stop_event.clear()
                update_thread = th.Thread(
                    target=(client.log_messages), args=(room_id, stop_event)
                )
                update_thread.start()
            else:
                print("Please select one of the options only.")
                continue
        else:
            message = input("> ")
            if message == "exit":
                print("Leaving the room...")
                client.unsubscribe(joined_room_id or "")
                joined_room_id = None
                is_chatting = False
                stop_event.set()
                client.con.close()
                update_thread.join()  # type: ignore
                print(f"\nYou left the room with {room_id=}")
                client.reinit_connection()
                continue

            client.send_to_room(joined_room_id or "", message)
