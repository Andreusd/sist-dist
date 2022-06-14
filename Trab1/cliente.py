import socket
import json
import random
import select
import multiprocessing
import sys

from comuns import *
from payloads import *
from messages import *


HOST_SERVIDOR = 'localhost'  # maquina onde esta o servidor
PORT_SERVIDOR = 10000       # porta que o servidor esta escutando

# aceita conexoes de todos os lugares
HOST_LOCAL = ''
# porta local eh definida aleatoriamente
PORT_LOCAL = random.randrange(5000, 10000)


clientes = {}  # lista de clientes fornecida pelo servidor
peerSockets = {}  # mapa de usuario para soquete


class Cliente(Conexao):
    '''classe que define as operações que o cliente executa'''

    def __init__(self, host: str, porta: int):
        # cria socket
        # Internet (IPv4 + TCP)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # conecta-se com o servidor
        sock.connect((host, porta))

        self.sock = sock

    def enviaPacote(self, payload: Payload, comResposta: bool = False):
        '''envia um pacote do lado do cliente'''
        self.envia(payload.toJson())
        if comResposta:
            conteudo = self.recebe()
            resposta = json.loads(conteudo)
            if resposta["status"] == 400:
                imprimeErro(f"Erro! {resposta['mensagem']}")
            return resposta


class ClienteCentral(Cliente):
    '''define as operacoes que o cliente realiza com o servidor central'''

    def __init__(self, host: str, porta: int):
        super().__init__(host, porta)

    def fazLogin(self, nome: str):
        return self.enviaPacote(Login(nome, PORT_LOCAL), True)

    def fazLogoff(self):
        return self.enviaPacote(Logoff(self.username), True)

    def pedeLista(self):
        return self.enviaPacote(GetLista(), True)

    def atualizaLista(self):
        global clientes
        clientes = self.pedeLista()["clientes"]
        imprimeListaFormatada(clientes)

    def escolheNome(self):
        '''escolhe o nome na entrada'''
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
    '''define as operacoes que um cliente envia para o outro peer'''

    def __init__(self, host: str, porta: int, nome: str):
        super().__init__(host, porta)
        self.username = nome

    def enviaMensagem(self, mensagem: str):
        self.enviaPacote(Mensagem(self.username, mensagem))


def conectaComPeer(mensagem: str, nomeOutro: str, nomeMeu: str):
    '''funcao que envia mensagens para um peer'''
    if nomeOutro not in clientes:
        imprimeErro(MESSAGE_RECIPIENT_DISCONECTED)
        return

    endrUser, portUser = clientes[nomeOutro].values()

    while True:
        try:
            # busca o sockete associado ao outro peer na lista caso contrario cria um novo
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
            # vou remove-lo da lista de socketes e tentar criar um novo
            peerSockets.pop(nomeOutro)


def printWelcomeMessage():
    '''funcao queexibe mensagem de boas vindas'''
    imprime("Bem vindo!", destaque=True)
    imprime(MESSAGE_WELCOME)
    imprime("", destaque=True)


def escutaPeers(conexao):
    '''funcao que executa concorrentemente recebendo mensagens de um peer'''
    cor = random.choice(cores)
    while True:
        data = conexao.recebe()
        if not data:  # dados vazios: cliente encerrou
            conexao.encerra()  # encerra a conexao com o cliente
            return
        pacote = json.loads(data)
        imprime(pacote["username"] + ' -> vc: ' +
                pacote["mensagem"], cor)


def escolheEntrada(clienteCentral: ClienteCentral, servidorLocal: Servidor):
    ''' loop principal da aplicacao'''
    processes = []
    listeningSockets = []
    talkingTo = None
    while True:
        leitura, _, _ = select.select((sys.stdin, servidorLocal.sock), (), ())
        for pronto in leitura:
            if pronto == servidorLocal.sock:  # pedido novo de conexao
                cliSock, _ = servidorLocal.aceitaConexao()
                conexao = Conexao(cliSock)
                peer = multiprocessing.Process(
                    target=escutaPeers, args=(conexao,))  # inicia novo processo cuja funcao eh escutar os peers
                peer.start()
                processes.append(peer)
                listeningSockets.append(cliSock)
            elif pronto == sys.stdin:  # entrada padrao
                comando = input()
                if comando == "logoff":  # inicia o processo de encerrar a aplicacao
                    clienteCentral.fazLogoff()  # envia o payload de logoff para o servidor central
                    clienteCentral.encerra()  # fecha o sockete com o servidor central
                    servidorLocal.encerra()  # encerra o sockete que aceita novas conversas com os peers
                    for p, s in zip(processes, listeningSockets):
                        s.close()  # fecha os socketes que escutam dos peers
                        p.terminate()  # encerra os processor que escutam dos peers
                    sys.exit()  # encerra a aplicacao
                elif comando == "lista":
                    clienteCentral.atualizaLista()  # atualiza a lista com o servidor e imprime
                elif comando == clienteCentral.username:  # nao permite conversar consigo mesmo
                    imprimeErro(ERROR_RECIPIENT_IS_USER)
                elif comando in clientes:
                    talkingTo = comando  # define com quem a conversa esta acontecendo
                    imprime(
                        f"Você está falando com {talkingTo}", destaque=True)
                elif talkingTo:  # envia mensagem para o peer
                    conectaComPeer(comando, talkingTo, clienteCentral.username)
                else:
                    imprimeErro(ERROR_USER_NOT_FOUND)


def main():
    '''funcao principal do cliente'''

    printWelcomeMessage()

    # inicia o cliente do servidor central
    try:
        clienteCentral = ClienteCentral(HOST_SERVIDOR, PORT_SERVIDOR)
    except ConnectionRefusedError:  # erro gerado se o servidor nao estiver executando
        imprimeErro(ERROR_SERVER_NOT_RUNNING)
        return

    # inicia o servidor local do cliente (peer)
    servidorLocal = Servidor(HOST_LOCAL, PORT_LOCAL)

    clienteCentral.escolheNome()  # escolhe o nome do cliente

    clienteCentral.atualizaLista()  # atualiza a lista automaticamente ao conectar

    escolheEntrada(clienteCentral, servidorLocal)  # inicia o loop principal


if __name__ == '__main__':
    main()
