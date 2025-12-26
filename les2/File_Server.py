import socket
import os

# Настройка TCP-сокета
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

PORT = 1234
server_socket.bind(('localhost', PORT))
server_socket.listen(5)
print("Ожидаем подключения...")

# Принимаем подключение
client_socket, client_address = server_socket.accept()
print(f"Подключился клиент с адресом: {client_address}")

BUFFER_SIZE = 4096

FILE_PATH_1 = "C:/Users/netrunner/Desktop/prfiles/les2/files/video.mp4"
FILE_PATH_RECV_1 = "C:/Users/netrunner/Desktop/prfiles/les2/results/received_video.mp4"

size_1 = os.path.getsize(FILE_PATH_1)
print(size_1)

to_send = f"{FILE_PATH_RECV_1};{str(size_1)};"
client_socket.send(to_send.encode('utf-8'))
# Читаем весь файл целиком
with open(FILE_PATH_1, "rb") as f: # r/rb/w/wb
    
    while True:
        chunk = f.read(BUFFER_SIZE)
        if not chunk:
            break
        # data_bytes += chunk
        client_socket.send(chunk)
        print(chunk)





print("Файл полностью отправлен!")

# Закрываем соединение
client_socket.close()
server_socket.close()
