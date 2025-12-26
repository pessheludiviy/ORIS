import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 1234))
print("Подключились к серверу")


BUFFER_SIZE = 4096  # размер буфера
received_img = 'C:/Users/netrunner/Desktop/prfiles/les2/results/received_video.mp4'

file_info_1 = client_socket.recv(BUFFER_SIZE)
file_ifo_splitted = file_info_1.split(";".encode('utf-8'))
print(file_ifo_splitted)


FILE_PATH_RECV_1 =  file_ifo_splitted[0].decode('utf-8')
print(FILE_PATH_RECV_1)
size_1 = file_ifo_splitted[1].decode('utf-8')
print(size_1)

start_file = file_ifo_splitted[2]
print(start_file)



with open(FILE_PATH_RECV_1, 'wb') as received_data:
    received_data.write(b"".join(file_ifo_splitted[2:]))
    while True:
        chunk = client_socket.recv(BUFFER_SIZE)
        if not chunk:
            break
        received_data.write(chunk)


client_socket.close()
