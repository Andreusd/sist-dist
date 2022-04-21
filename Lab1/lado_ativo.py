# Aluno Andre Uziel 119051475 2022.1

import socket

HOST = 'localhost'
PORT = 5000

sock = socket.socket()

sock.connect((HOST, PORT))

while msg := input().encode():  # encerra quando o usuário digitar uma mensagem vazia
    # operador := disponivel no python 3.8 (faz atribuição e retorna o resultado)
    sock.send(msg)
    ans = sock.recv(1024)
    print(str(ans, encoding='utf-8'))

sock.close()
