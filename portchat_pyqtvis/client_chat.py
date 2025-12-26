import socket
import threading
import sys
import json
from PyQt6.QtCore import QObject, pyqtSignal


class ChatClient(QObject):
    received_signal = pyqtSignal(dict)

    def __init__(self, host='127.0.0.1', port=12345):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.active = False
        self.current_room = None
        self.username = "Anonymous"

    def connect_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            self.active = True
            print("[СОЕДИНЕНИЕ] Установлено с сервером")
            threading.Thread(target=self.listen_server, daemon=True).start()
            return True
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            return False

    def disconnect_server(self):
        self.active = False
        if self.sock:
            self.sock.close()
            print("Клиент отключен")

    def send_command(self, command):
        if self.sock:
            try:
                self.sock.send(json.dumps(command).encode('utf-8'))
            except Exception as e:
                print(f"[ОШИБКА] {e}")

    def listen_server(self):
        try:
            while self.active:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    print("[ОТКЛЮЧЕНИЕ] Соединение разорвано сервером")
                    break
                self.process_message(json.loads(data))
        except Exception as e:
            print(f"[ОШИБКА] {e}")
        finally:
            self.active = False

    def process_message(self, msg):
        msg_type = msg.get('type')
        if msg_type == 'room_joined':
            self.current_room = msg.get('room')
        elif msg_type == 'info':
            print(f"[ИНФО] {msg.get('text')}")
        elif msg_type == 'error':
            print(f"[ОШИБКА] {msg.get('text')}")
        self.received_signal.emit(msg)

    def join_room(self, room, username=None):
        if username:
            self.username = username
        self.send_command({"cmd": "join", "room": room, "username": self.username})

    def send_message(self, text):
        if not self.current_room:
            return False
        self.send_command({"cmd": "msg", "text": text})
        return True

    def leave_room(self):
        self.send_command({"cmd": "leave"})
        self.current_room = None
