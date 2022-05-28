import socket
import json
import random
import select
import threading
import sys

HOST_SERVIDOR = 'localhost'  # maquina onde esta o servidor
PORT_SERVIDOR = 10000       # porta que o servidor esta escutando

HOST_LOCAL = ''
PORT_LOCAL = random.randrange(5000, 10000)

entradas = [sys.stdin]


def iniciaCliente(host, porta):
    '''Cria um socket de cliente e conecta-se ao servidor.
    Saida: socket criado'''
    # cria socket
    # Internet (IPv4 + TCP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta-se com o servidor
    sock.connect((host, porta))

    return sock


def aceitaConexao(sock):
    '''Aceita o pedido de conexao de um cliente
    Entrada: o socket do servidor
    Saida: o novo socket da conexao e o endereco do cliente'''

    # estabelece conexao com o proximo cliente
    clisock, endr = sock.accept()

    return clisock, endr[0]


def iniciaServidor(host: str, porta: int):
    '''Cria um socket de servidor e o coloca em modo de espera por conexoes
    Saida: o socket criado'''
    # cria o socket
    # Internet( IPv4 + TCP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # evita bug de socket already in use quando o servidor termina abruptamente
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # vincula a localizacao do servidor
    sock.bind((host, porta))

    # coloca-se em modo de espera por conexoes
    sock.listen(100)

    # configura o socket para o modo nao-bloqueante
    sock.setblocking(False)

    # inclui o socket principal na lista de entradas de interesse
    entradas.append(sock)

    return sock


def iniciaConversa(cliSock: socket.socket, username: str):
    while True:

        leitura, _, _ = select.select((sys.stdin, cliSock), [], [])

        for pronto in leitura:

            if pronto == cliSock:

                data = cliSock.recv(1024)

                if not data:  # dados vazios: cliente encerrou
                    cliSock.close()  # encerra a conexao com o cliente
                    return

                pacote = json.loads(str(data, encoding='utf-8'))

                print(pacote["username"] + ': '+pacote["mensagem"])

            elif pronto == sys.stdin:

                mensagem = input()

                if mensagem == '/leave':
                    return

                pacote = json.dumps(
                    {"username": username, "mensagem": mensagem})

                cliSock.sendall(pacote.encode("utf-8"))


def enviaPacote(sock, operacao, username=""):

    requisicao = {"operacao": operacao,
                  "username": username, "porta": PORT_LOCAL}
    payload = json.dumps(requisicao)
    sock.sendall(payload.encode('utf-8'))

    payload_resposta = str(sock.recv(1024), encoding='utf-8')
    resposta = json.loads(payload_resposta)
    print(resposta)

    return resposta


def pegaLista(sock):

    resposta = enviaPacote(sock, operacao="get_lista")

    return resposta["clientes"]


def fazRequisicoes(sock):
    '''Faz requisicoes ao servidor e exibe o resultado.
    Entrada: socket conectado ao servidor'''

    while True:

        username = input("Entre com o seu username: ")
        if username == 'fim':
            return

        resposta = enviaPacote(sock, operacao="login", username=username)

        if(resposta["status"] == 200):
            break

    hostSock = iniciaServidor(HOST_LOCAL, PORT_LOCAL)

    lista_usuarios = pegaLista(sock)

    while True:

        leitura, _, _ = select.select(entradas, [], [])

        for pronto in leitura:

            if pronto == hostSock:  # pedido novo de conexao

                print("alguem quer falar comigo!")

                cliSock, endr = aceitaConexao(hostSock)

                # cria novo processo para atender o cliente
                iniciaConversa(cliSock, username)

            elif pronto == sys.stdin:  # entrada padrao

                operacao = input()

                if operacao == "logoff":

                    resposta = enviaPacote(
                        sock, operacao=operacao, username=username)

                    sock.close()
                    return

                elif operacao == "get_lista":
                    pegaLista(sock)

                elif operacao in lista_usuarios:

                    print("quero falar com alguem!")

                    endrUser, portUser = lista_usuarios[operacao].values()

                    cliSock = iniciaCliente(endrUser, portUser)

                    iniciaConversa(cliSock, username)


def main():
    '''Funcao principal do cliente'''
    # inicia o cliente
    sock = iniciaCliente(HOST_SERVIDOR, PORT_SERVIDOR)
    # interage com o servidor ate encerrar
    fazRequisicoes(sock)


main()
