from socket import AF_INET, SOCK_STREAM, socket, SOL_SOCKET, SO_REUSEADDR

# Конфигурация
HOST = 'localhost'
PORT = 1234
CHUNK_SIZE = 1024 # размер чанка

# Создаем TCP-сокет
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print("Ожидаем подключения...")

client_socket, client_address = server_socket.accept()

# Получим дескрипторы сокетов
server_descriptor = server_socket.fileno()
client_descriptor = client_socket.fileno()

print("\n--- Информация о соединении ---")
print(f"Дескриптор серверного сокета: {server_descriptor}")
print(f"Дескриптор клиентского сокета: {client_descriptor}")
print(f"Адрес клиента: {client_address}")

# Отправляем большое сообщение целиком
large_message = "Привет! У меня нет фантазии, поэтому мы делаем большое сообщение так. Пока!" * 50
message_bytes = large_message.encode('utf-8')

print(f"\nОтправляем сообщение размером {len(message_bytes)} байт")

# Отправляем данные чанками
for i in range(0, len(message_bytes), CHUNK_SIZE):
    chunk = message_bytes[i:i+CHUNK_SIZE]
    client_socket.send(chunk)

print("Все данные отправлены!")

# Закрываем соединение
client_socket.close()
server_socket.close()
print("\nСоединения закрыты. Пока!")