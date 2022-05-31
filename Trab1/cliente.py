import socket
import json
import random
import select
import threading
import sys

from comuns import *
from payloads import *
from messages import *


HOST_SERVIDOR = 'localhost'  # maquina onde esta o servidor
PORT_SERVIDOR = 10000       # porta que o servidor esta escutando

HOST_LOCAL = ''
PORT_LOCAL = random.randrange(5000, 10000)

entradas = [sys.stdin]
clientes = {}  # lista de clientes fornecida pelo servidor
peerSockets = {}  # mapa de usuario para soquete


class Cliente:
    def __init__(self, host: str, porta: int):
        # cria socket
        # Internet (IPv4 + TCP)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # conecta-se com o servidor
        sock.connect((host, porta))

        self.sock = sock

    def enviaPacote(self, payload: dict, comResposta: bool = False):
        imprimeDebug(json.dumps(payload))
        self.sock.sendall(json.dumps(payload).encode('utf-8'))
        if comResposta:
            resposta = json.loads(str(self.sock.recv(1024), encoding='utf-8'))
            if resposta["status"] == 400:
                imprimeErro(f"Erro! {resposta['mensagem']}")
            return resposta


class ClienteCentral(Cliente):
    def __init__(self, host: str, porta: int):
        super().__init__(host, porta)

    def fazLogin(self, nome: str):
        return self.enviaPacote(Login(nome, PORT_LOCAL), True)

    def fazLogoff(self):
        return self.enviaPacote(Logoff(self.username), True)

    def pedeLista(self):
        return self.enviaPacote(GetLista, True)

    def atualizaLista(self):
        global clientes
        clientes = self.pedeLista()["clientes"]
        imprimeListaFormatada(clientes)

    def escolheNome(self):
        msgUsername = "Entre com o seu username: "
        nome = sys.argv[1] if len(sys.argv) > 1 else input(
            msgUsername)
        while True:
            resposta = self.fazLogin(nome)
            if(resposta["status"] == 200):
                break
            nome = input(msgUsername)
        self.username = nome

    def encerra(self):
        self.sock.close()


class PeerAtivo(Cliente):
    def __init__(self, host: str, porta: int, nome: str):
        super().__init__(host, porta)
        self.username = nome

    def enviaMensagem(self, mensagem: str):
        self.enviaPacote(Mensagem(self.username, mensagem))


def conectaComPeer(mensagem: str, nomeOutro: str, nomeMeu: str):
    imprimeDebug("quero falar com alguem!")

    if nomeOutro not in clientes:
        imprimeErro(MESSAGE_RECIPIENT_DISCONECTED)
        return

    endrUser, portUser = clientes[nomeOutro].values()

    while True:
        try:
            peer = peerSockets[nomeOutro] if nomeOutro in peerSockets else PeerAtivo(
                endrUser, portUser, nomeMeu)
        except ConnectionRefusedError:  # 1o caso: o destinatário se desconectou
            imprimeErro(ERROR_RECIPIENT_DISCONECTED)
            break
        try:
            peer.enviaMensagem(mensagem)
            peerSockets[nomeOutro] = peer
            break
        except BrokenPipeError:  # 2o caso: um sockete que usamos anteriormente não é mais válido
            # vou remove-lo da lista e tentar conectar novamente
            peerSockets.pop(nomeOutro)


def printWelcomeMessage():
    imprime("Bem vindo!", destaque=True)
    imprime(MESSAGE_WELCOME)
    imprime("", destaque=True)


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
        data = cliSock.recv(1024)
        if not data:  # dados vazios: cliente encerrou
            cliSock.close()  # encerra a conexao com o cliente
            return
        pacote = json.loads(str(data, encoding='utf-8'))
        imprime(pacote["username"] + ' -> vc: ' +
                pacote["mensagem"], cor)


def escolheEntrada(clienteCentral: ClienteCentral, servidorLocal: Servidor):
    talkingTo = None
    while True:
        leitura, _, _ = select.select(entradas, [], [])
        for pronto in leitura:
            if pronto == servidorLocal.sock:  # pedido novo de conexao
                imprimeDebug("alguem quer falar comigo!")
                cliSock, _ = servidorLocal.aceitaConexao()
                peer = threading.Thread(
                    target=escutaPeers, args=(cliSock,))
                peer.start()
            elif pronto == sys.stdin:  # entrada padrao
                comando = input()
                if comando == "logoff":
                    resposta = clienteCentral.fazLogoff()
                    clienteCentral.encerra()
                    servidorLocal.encerra()
                    sys.exit()
                elif comando == "lista":
                    clienteCentral.atualizaLista()
                elif comando == clienteCentral.username:
                    imprimeErro(ERROR_RECIPIENT_IS_USER)
                elif comando in clientes:
                    talkingTo = comando
                    imprime(
                        f"Você está falando com {talkingTo}", destaque=True)
                elif talkingTo:
                    conectaComPeer(comando, talkingTo, clienteCentral.username)
                else:
                    imprimeErro(ERROR_USER_NOT_FOUND)


def main():
    '''Funcao principal do cliente'''

    printWelcomeMessage()

    # inicia o cliente
    try:
        clienteCentral = ClienteCentral(HOST_SERVIDOR, PORT_SERVIDOR)
    except ConnectionRefusedError:
        imprimeErro(ERROR_SERVER_NOT_RUNNING)
        return

    servidorLocal = Servidor(HOST_LOCAL, PORT_LOCAL, entradas)

    clienteCentral.escolheNome()

    clienteCentral.atualizaLista()

    escolheEntrada(clienteCentral, servidorLocal)


main()
