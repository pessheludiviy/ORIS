import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 1234))

print("Все ок. Мы подключились к серверу")

BUFFER_SIZE = 4096  # размер буфера при приёме
received_data = b""  # сюда будем собирать все байты

print(client_socket.fileno())

while True:
    chunk = client_socket.recv(BUFFER_SIZE)
    if not chunk:  # если пришёл пустой чанк, значит сервер закончил
        break
    print(f"Получен чанк размером {len(chunk)} байт")
    received_data += chunk

# Декодируем и выводим
print("Получено от сервера:", received_data.decode('utf-8'))

client_socket.close()
