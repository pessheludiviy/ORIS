import socket
import threading
import json


class ChatServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.clients = {}
        self.channels = {}
        self.lock = threading.Lock()

    def run_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with self.sock:
            self.sock.bind((self.host, self.port))
            self.sock.listen()
            print(f"[СЕРВЕР АКТИВЕН] {self.host} : {self.port}")
            while True:
                conn, addr = self.sock.accept()
                print(f"Новое подключение: {addr}")
                with self.lock:
                    self.clients[conn] = {'username': f"User{addr[1]}", 'channel': None}
                self.dispatch_message(conn, {'type': 'info', 'text': 'Добро пожаловать в чат!'})
                threading.Thread(target=self.manage_client, args=(conn, addr), daemon=True).start()

    def dispatch_message(self, conn, message_dict):
        try:
            conn.sendall(json.dumps(message_dict).encode('utf-8'))
        except ConnectionResetError:
            self.disconnect_client(conn)

    def broadcast_channel(self, channel_name, message):
        with self.lock:
            if channel_name in self.channels:
                for conn in self.channels[channel_name]:
                    try:
                        self.dispatch_message(conn, message)
                    except:
                        self.disconnect_client(conn)

    def disconnect_client(self, conn):
        with self.lock:
            for channel_name, members in list(self.channels.items()):
                if conn in members:
                    members.remove(conn)
                if not members:
                    del self.channels[channel_name]
                else:
                    if conn in self.clients:
                        msg = {"type": "message", "from": "server",
                               "text": f"{self.clients[conn]['username']} вышел из комнаты"}
                        self.broadcast_channel(channel_name, msg)
            if conn in self.clients:
                del self.clients[conn]

    def manage_client(self, conn, addr):
        active_channel = None
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                message = json.loads(data)
                command = message.get('cmd', '').lower()

                if command == "exit":
                    self.dispatch_message(conn, {"type": "info", "text": "До свидания!"})
                    break

                if command == "join":
                    channel_name = message.get('room', '')
                    username = message.get('username', f"User{addr[1]}")
                    if not channel_name:
                        self.dispatch_message(conn, {"type": "error", "text": "Укажите имя комнаты"})
                        continue
                    with self.lock:
                        self.clients[conn]['username'] = username
                        prev_channel = self.clients[conn].get('channel')
                        if channel_name not in self.channels:
                            self.channels[channel_name] = []
                        if prev_channel and prev_channel in self.channels and conn in self.channels[prev_channel]:
                            self.channels[prev_channel].remove(conn)
                            if not self.channels[prev_channel]:
                                del self.channels[prev_channel]
                            else:
                                leave_msg = {"type": "info", "from": "server",
                                             "text": f"{self.clients[conn]['username']} покинул комнату"}
                                self.broadcast_channel(prev_channel, leave_msg)
                        self.channels[channel_name].append(conn)
                        self.clients[conn]['channel'] = channel_name
                        active_channel = channel_name
                    self.dispatch_message(conn, {"type": "room_joined", "room": channel_name})
                    join_msg = {"type": "info", "from": "server",
                                "text": f"{self.clients[conn]['username']} присоединился к комнате"}
                    self.broadcast_channel(channel_name, join_msg)

                elif command == "leave":
                    if not active_channel:
                        self.dispatch_message(conn, {"type": "error", "text": "Вы не находитесь в комнате"})
                        continue
                    with self.lock:
                        if active_channel and active_channel in self.channels and conn in self.channels[active_channel]:
                            self.channels[active_channel].remove(conn)
                            self.clients[conn]['channel'] = None
                            if not self.channels[active_channel]:
                                del self.channels[active_channel]
                            else:
                                leave_msg = {"type": "info", "from": "server",
                                             "text": f"{self.clients[conn]['username']} покинул комнату"}
                                self.broadcast_channel(active_channel, leave_msg)
                    self.dispatch_message(conn, {"type": "info", "text": "Вы покинули комнату"})
                    active_channel = None

                elif command in ['msg', 'message']:
                    msg_text = message.get('text', '')
                    username = self.clients[conn].get('username')
                    active_channel = self.clients[conn].get('channel')
                    if not msg_text:
                        self.dispatch_message(conn, {"type": "error", "text": "Введите сообщение"})
                        continue
                    if not active_channel:
                        self.dispatch_message(conn, {"type": "error", "text": "Вы не находитесь в комнате"})
                        continue
                    if active_channel in self.channels and conn in self.channels[active_channel]:
                        msg = {"type": "message", "from": username, "text": msg_text}
                        print(f"[СООБЩЕНИЕ] {active_channel} - {username} : {msg_text}")
                        self.broadcast_channel(active_channel, msg)
                    else:
                        self.dispatch_message(conn, {"type": "error", "text": "Вы не находитесь в комнате"})

                else:
                    self.dispatch_message(conn, {"type": "error", "text": "Неизвестная команда"})

        except ConnectionResetError:
            print(f"[ОТКЛЮЧЕНИЕ] Клиент {addr} прервал соединение")
        finally:
            self.disconnect_client(conn)
            conn.close()
            print(f"Клиент отключен {addr}")


if __name__ == "__main__":
    ChatServer().run_server()
