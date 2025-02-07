import socket
import json
import os
from uuid import uuid4
import threading


class User:
    server_address = ("0.0.0.0", 2055)

    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        self.con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.register()

    def register(self):
        self.con.sendto(
            json.dumps(
                {"name": self.name, "id": self.id, "request": "register"}
            ).encode(),
            User.server_address,
        )
        self.con.recvfrom(1024)

    def request_for_user_list(self):
        self.con.sendto(
            json.dumps(
                {"name": self.name, "id": self.id, "request": "list-users"}
            ).encode(),
            User.server_address,
        )
        data, _ = self.con.recvfrom(4096)
        response = json.loads(data.decode())
        if response.get("success"):
            print("%-6s\t%s" % ("ID", "User Name"))
            for user in response.get("message", []):
                print(f"{user['id']}\t{user['name']}")

    def send_file(self, target_user_id: str, filepath: str):
        if not os.path.exists(filepath):
            print("File not found.")
            return

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        self.con.sendto(
            json.dumps(
                {
                    "user_name": self.name,
                    "id": self.id,
                    "request": "send-file",
                    "target_user_id": target_user_id,
                    "filename": filename,
                    "filesize": filesize,
                }
            ).encode(),
            User.server_address,
        )

        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                self.con.sendto(
                    json.dumps(
                        {
                            "request": "file-chunk",
                            "target_user_id": target_user_id,
                            "filename": filename,
                            "chunk": chunk.hex(),
                        }
                    ).encode(),
                    User.server_address,
                )

        print(f"File '{filename}' sent to {target_user_id}")

    def request_file(self, target_user_id: str, filename: str):
        self.con.sendto(
            json.dumps(
                {
                    "user_name": self.name,
                    "id": self.id,
                    "request": "request-file",
                    "target_user_id": target_user_id,
                    "filename": filename,
                }
            ).encode(),
            User.server_address,
        )

    def approve_file_request(self, sender_id: str, filename: str):
        self.con.sendto(
            json.dumps(
                {
                    "request": "approve-file-request",
                    "sender_id": sender_id,
                    "filename": filename,
                }
            ).encode(),
            User.server_address,
        )

    def log_messages(self, stop_event: threading.Event):
        received_files = {}

        while not stop_event.is_set():
            try:
                data, _ = self.con.recvfrom(4096)
                response = json.loads(data.decode())
                request_type = response.get("request")

                if request_type == "file-chunk":
                    filename = response.get("filename")
                    chunk = bytes.fromhex(response.get("chunk"))

                    if filename not in received_files:
                        received_files[filename] = b""

                    received_files[filename] += chunk

                elif request_type == "file-request-approved":
                    print(
                        f"File request approved. Waiting to receive {response['filename']}..."
                    )

                elif request_type == "file-transfer-complete":
                    filename = response.get("filename")
                    with open(filename, "wb") as f:
                        f.write(received_files[filename])
                    print(f"\nFile '{filename}' received successfully!")
                    del received_files[filename]

            except OSError:
                pass
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}, Data: {data}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    name = input("Enter your name: ")
    user_id = str(uuid4()).split("-")[1]
    user = User(name, user_id)

    stop_event = threading.Event()
    log_thread = threading.Thread(target=user.log_messages, args=(stop_event,))
    # log_thread.start()

    while True:
        print("""\nOptions:
1. List users
2. Send File
3. Request File
4. Approve File Request
q. Exit""")
        choice = input("> ").lower()
        if choice == "q":
            stop_event.set()
            user.con.close()
            log_thread.join()
            exit()
        elif choice == "1":
            user.request_for_user_list()
        elif choice == "2":
            user.request_for_user_list()
            target_user_id = input("Target user ID: ")
            filepath = input("Enter file path: ")
            user.send_file(target_user_id, filepath)
        elif choice == "3":
            user.request_for_user_list()
            target_user_id = input("Target user ID: ")
            filename = input("Enter filename: ")
            user.request_file(target_user_id, filename)
        elif choice == "4":
            sender_id = input("Sender ID: ")
            filename = input("Filename: ")
            user.approve_file_request(sender_id, filename)
        else:
            print("Invalid choice.")
