import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QApplication
from PyQt6.QtCore import QSize, Qt
from client_chat import ChatClient


class ChatMessageWidget(QWidget):
    def __init__(self, author='Anonymous', content=''):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 8, 15, 8)
        self.name_label = QLabel(author)
        self.name_label.setStyleSheet("font-weight: bold; color: #90EE90;")
        layout.addWidget(self.name_label)
        self.text_label = QLabel(content)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #FFFFFF;")
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.text_label)
        self.setLayout(layout)

    def sizeHint(self):
        return QSize(400, 60)


class ChatInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat")
        self.client = ChatClient()
        self.client.received_signal.connect(self.handle_server_event)
        if not self.client.connect_server():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к серверу")
            sys.exit(1)
        layout = QVBoxLayout(self)
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Введите номер комнаты...")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите ваше имя...")
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите сообщение...")
        self.message_input.returnPressed.connect(self.send_message)
        self.join_button = QPushButton("Присоединиться к комнате")
        self.send_button = QPushButton("Отправить сообщение")
        self.leave_button = QPushButton("Покинуть комнату")
        self.messages_list = QListWidget()
        layout.addWidget(QLabel("Комната:"))
        layout.addWidget(self.room_input)
        layout.addWidget(QLabel("Ваше имя:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Сообщение:"))
        layout.addWidget(self.message_input)
        layout.addWidget(self.join_button)
        layout.addWidget(self.send_button)
        layout.addWidget(self.leave_button)
        layout.addWidget(QLabel("Сообщения:"))
        layout.addWidget(self.messages_list)
        self.setLayout(layout)
        self.join_button.clicked.connect(self.join_room)
        self.send_button.clicked.connect(self.send_message)
        self.leave_button.clicked.connect(self.leave_room)

    def join_room(self):
        room_number = self.room_input.text().strip()
        username = self.username_input.text().strip()
        if room_number:
            self.client.username = username
            self.client.join_room(room_number, username)

    def send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        if text and self.client.current_room:
            if self.client.send_message(text):
                self.message_input.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Сообщение не отправлено")
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала присоединитесь к комнате")

    def leave_room(self):
        if self.client.current_room:
            self.client.leave_room()
            self.add_message("Система", "Вы покинули комнату")
        else:
            QMessageBox.information(self, "Информация", "Вы не находитесь в комнате")

    def add_message(self, author, content):
        widget = ChatMessageWidget(author, content)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.messages_list.addItem(item)
        self.messages_list.setItemWidget(item, widget)
        self.messages_list.scrollToBottom()

    def handle_server_event(self, msg):
        msg_type = msg.get('type')
        content = msg.get('text', '')
        sender = msg.get('from', 'Система')
        if msg_type == 'message':
            self.add_message(sender, content)
        elif msg_type in ['info', 'room_joined']:
            self.add_message("Система", content)
        elif msg_type == 'error':
            QMessageBox.warning(self, "Ошибка", content)

    def closeEvent(self, event):
        self.client.disconnect_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.show()
    app.exec()
