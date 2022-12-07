import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('192.168.194.26',1002))
server.listen()

client_socket, client_address = server.accept()

file = open('1.jpg', 'wb')
image_chunk = client_socket.recv(2048)

while image_chunk:
    file.write(image_chunk)
    image_chunk = client_socket.recv(2048)

file.close()
client_socket.close()