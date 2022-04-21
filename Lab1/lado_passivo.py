# Aluno Andre Uziel 119051475 2022.1

import socket

HOST = ''
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((HOST, PORT))

sock.listen(1)

newSock, addr = sock.accept()
print("Conectado com:" + str(addr))

while True:
    msg = newSock.recv(1024)
    if not msg:
        break
    newSock.send(b'echo ' + msg)

newSock.close()
sock.close()
