# Импортируем либу, чтобы работать с сокетами
from socket import AF_INET, SOCK_STREAM, socket, SOL_SOCKET, SO_REUSEADDR

# Создаём TCP-сокет
server_socket = socket(AF_INET, SOCK_STREAM) # AF_INET - используем IPv4, SOCK_STREAM - используем TCP (потоковый протокол)
# setsockopt задаёт настройки работы сокета
# SOL_SOCKET - настраиваем сам сокет (а не протокол)
# SO_REUSEADDR разрешает повторно использовать адрес
# (Когда сервер закрылся, порт уходит в состояние TIME_WAIT (ОС держит его ещё секунд 30–60))
# 1 - включить эту настрйоку, 0 - выключить эту настройку
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

PORT = 1234 # выбранный нами порт (можно от 1024 до 65535)

#Привязываем сокет к адресу и порту
server_socket.bind(('localhost', PORT)) # 'localhost' - наш комплюктер

# Начинаем прослушивать входящие подключения
server_socket.listen(5) # размер очереди из клиентов, которые могут ждать подключения
print(f"Сервер запущен на localhost:{PORT}. Ожидаем подключения...")

# Принимаем подключение
client_socket, client_address = server_socket.accept()
print(f"Подключился клиент с адресом: {client_address}")
print(f"Подключился клиент с адресом: {client_socket}")

# Отправляем данные клиенту
russian_text = "Диана, привет!"
client_socket.send(russian_text.encode('utf-8'))

data = client_socket.recv(1024)
print("Получено от клиента:", data.decode('utf-8'))
# Закрываем соединение с клиентом

client_socket.close()

# Закрываем сокет (опционально)
# server_socket.close()