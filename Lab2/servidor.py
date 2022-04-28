# Aluno Andre Uziel 119051475 2022.1

import socket

from funcoes import palavras_mais_frequentes

HOST = ''
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((HOST, PORT))

sock.listen(1)

while True:
    newSock, addr = sock.accept()
    print("Conectado com:" + str(addr))
    # cliente informa o nome do arquivo
    while msg := newSock.recv(1024):  # operador := disponivel no python 3.8
        # digitar uma mensagem vazia encerra a conexao com o cliente
        try:
            # tenta abrir o arquivo com o nome que o cliente forneceu
            with open(file=str(msg, encoding='utf-8'), mode='r', encoding='utf-8') as arquivo:
                texto = arquivo.read()
            # envia o conteudo do arquivo tratado para o cliente
            newSock.send(palavras_mais_frequentes(texto).encode())
        # captura a excessao quando nao acha o arquivo
        except FileNotFoundError:
            newSock.send(b"Erro: o arquivo nao foi encontrado")

    newSock.close()
sock.close()
