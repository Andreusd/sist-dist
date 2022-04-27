# Aluno Andre Uziel 119051475 2022.1

import socket
import re

from funcoes import palavras_mais_frequentes

HOST = ''
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((HOST, PORT))

sock.listen(1)

while True:

    newSock, addr = sock.accept()
    print("Conectado com:" + str(addr))

    while True:
        msg = newSock.recv(1024)
        if not msg:
            break
        try:
            with open(file=str(msg, encoding='utf-8'), mode='r', encoding='utf-8') as arquivo:
                texto = arquivo.read()
            newSock.send(palavras_mais_frequentes(texto).encode())
        except FileNotFoundError:
            newSock.send(b"Erro: o arquivo nao foi encontrado")

    newSock.close()
    sock.close()
