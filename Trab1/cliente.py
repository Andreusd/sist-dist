import socket
import json
import random
import select
import threading
import sys

from comuns import *
from payloads_cliente import *
from error_messages import *


HOST_SERVIDOR = 'localhost'  # maquina onde esta o servidor
PORT_SERVIDOR = 10000       # porta que o servidor esta escutando

HOST_LOCAL = ''
PORT_LOCAL = random.randrange(5000, 10000)

entradas = [sys.stdin]
clientes = {}  # lista de clientes fornecida pelo servidor
peerSockets = {}  # mapa de usuario para soquete


def iniciaCliente(host: str, porta: int):
    '''Cria um socket de cliente e conecta-se ao servidor.
    Saida: socket criado'''
    # cria socket
    # Internet (IPv4 + TCP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # conecta-se com o servidor
    sock.connect((host, porta))

    return sock


def salvaMensagem(pacote: dict, nomeMeu: str):
    pass
    log = []
    try:
        with open(f"{nomeMeu}_log.json", "r") as arquivo:
            conteudo = arquivo.read()
            log = json.loads(conteudo)
    except FileNotFoundError:
        pass
    log.append(pacote)
    payload = json.dumps(log)
    with open(f"{nomeMeu}_log.json", "w") as arquivo:
        arquivo.write(payload)


def escutaPeers(cliSock: socket):
    cor = random.choice(cores)
    while True:
        leitura, _, _ = select.select((cliSock, sys.stdin), [], [])
        for pronto in leitura:
            if pronto == cliSock:
                data = cliSock.recv(1024)
                if not data:  # dados vazios: cliente encerrou
                    cliSock.close()  # encerra a conexao com o cliente
                    return
                pacote = json.loads(str(data, encoding='utf-8'))
                imprime(pacote["username"] + ' -> vc: ' +
                        pacote["mensagem"], cor)
            elif pronto == sys.stdin and input() == "logoff":
                cliSock.close()
                return


def imprimeErroSeHouver(resposta: dict):
    if resposta["status"] == 400:
        imprime(f"Erro! {resposta['mensagem']}")


def enviaPacote(sock: socket.socket, payload: str, comResposta: bool = False):
    sock.sendall(json.dumps(payload).encode('utf-8'))
    return json.loads(str(sock.recv(1024), encoding='utf-8')) if comResposta else None


def operacaoLogin(sock: socket.socket, username: str):
    return enviaPacote(sock, Login(username, PORT_LOCAL), True)


def operacaoLogoff(sock: socket.socket, username: str):
    return enviaPacote(sock, Logoff(username), True)


def operacaoGetLista(sock: socket.socket):
    return enviaPacote(sock, GetLista, True)


def atualizaLista(sock: socket.socket) -> dict:
    global clientes
    clientes = operacaoGetLista(sock)["clientes"]
    imprimeListaFormatada(clientes)


def conectaComPeer(mensagem: str, nomeOutro: str, nomeMeu: str):
    imprimeDebug("quero falar com alguem!")

    endrUser, portUser = clientes[nomeOutro].values()

    while True:
        try:
            cliSock = peerSockets[nomeOutro] if nomeOutro in peerSockets else iniciaCliente(
                endrUser, portUser)
        except ConnectionRefusedError:  # 1o caso: o destinatário se desconectou
            print("1o caso: o destinatário se desconectou")
            imprime(ERROR_RECIPIENT_DISCONECTED)
            break
        try:
            enviaPacote(cliSock, Mensagem(nomeMeu, mensagem))
            peerSockets[nomeOutro] = cliSock
            break
        except ConnectionRefusedError:  # 2o caso: um sockete que usamos anteriormente não é mais válido
            print("2o caso: um sockete que usamos anteriormente não é mais válido")
            peerSockets.pop(nomeOutro)


def escolheNome(sock: socket.socket):
    msgUsername = "Entre com o seu username: "
    nomeMeu = sys.argv[1] if len(sys.argv) > 1 else input(
        msgUsername)
    while True:
        resposta = operacaoLogin(sock, nomeMeu)
        if(resposta["status"] == 200):
            break
        nomeMeu = input(msgUsername)
    return nomeMeu


def escolheEntrada(centralSock: socket.socket, hostSock: socket.socket, nomeMeu: str):
    talkingTo = None
    while True:
        leitura, _, _ = select.select(entradas, [], [])
        for pronto in leitura:
            if pronto == hostSock:  # pedido novo de conexao
                imprimeDebug("alguem quer falar comigo!")
                cliSock, _ = aceitaConexao(hostSock)
                peer = threading.Thread(
                    target=escutaPeers, args=(cliSock,))
                peer.start()
            elif pronto == sys.stdin:  # entrada padrao
                comando = input()
                if comando == "logoff":
                    resposta = operacaoLogoff(centralSock, nomeMeu)
                    centralSock.close()
                    hostSock.close()
                    return
                elif comando == "lista":
                    atualizaLista(centralSock)
                elif comando == nomeMeu:
                    imprime(ERROR_RECIPIENT_IS_USER)
                elif comando in clientes:
                    talkingTo = comando
                    imprime(
                        f"Você está falando com {talkingTo}".center(40, "-"))
                elif talkingTo:
                    conectaComPeer(comando, talkingTo, nomeMeu)
                else:
                    imprime(ERROR_USER_NOT_FOUND)


def fazRequisicoes(centralSock: socket.socket, hostSock: socket.socket):
    '''Faz requisicoes ao servidor e exibe o resultado.
    Entrada: socket conectado ao servidor'''

    nomeMeu = escolheNome(centralSock)

    atualizaLista(centralSock)

    escolheEntrada(centralSock, hostSock, nomeMeu)


def main():
    '''Funcao principal do cliente'''
    # inicia o cliente
    centralSock = iniciaCliente(HOST_SERVIDOR, PORT_SERVIDOR)

    hostSock = iniciaServidor(HOST_LOCAL, PORT_LOCAL, entradas)
    # interage com o servidor ate encerrar
    fazRequisicoes(centralSock, hostSock)


main()
