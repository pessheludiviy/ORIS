# Также пимпортим либу, чтобы работать с сокетами
import socket

# Создаём такой же TCP сокет
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Подключаемся к серверу
client_socket.connect(('localhost', 1234))

print("Все ок. Мы подключились к серверу")

# Получаем данные от сервера
data = client_socket.recv(1024)

print("Получено от сервера:", data.decode('utf-8')) # данные приходят в виде байтов, поэтому декодируем их в строку

russian_text = input('пиши')
client_socket.send(russian_text.encode('utf-8'))

# Закрываем сокет
client_socket.close()