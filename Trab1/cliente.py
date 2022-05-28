import socket
import json
import random
import select
import threading
import sys

from comuns import *
from payloads_cliente import *
from errors import *

HOST_SERVIDOR = 'localhost'  # maquina onde esta o servidor
PORT_SERVIDOR = 10000       # porta que o servidor esta escutando

HOST_LOCAL = ''
PORT_LOCAL = random.randrange(5000, 10000)

entradas = [sys.stdin]
clientes = {}


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


def iniciaConversa(cliSock: socket, nomeMeu: str):
    while True:
        leitura, _, _ = select.select((sys.stdin, cliSock), [], [])
        for pronto in leitura:
            if pronto == cliSock:
                data = cliSock.recv(1024)
                if not data:  # dados vazios: cliente encerrou
                    cliSock.close()  # encerra a conexao com o cliente
                    return
                pacote = json.loads(str(data, encoding='utf-8'))
                salvaMensagem(pacote, nomeMeu)
                print(pacote["username"] + ': '+pacote["mensagem"])
            elif pronto == sys.stdin:
                mensagem = input()
                if mensagem == 'leave':
                    cliSock.close()
                    return
                pacote = Mensagem(nomeMeu, mensagem)
                salvaMensagem(pacote, nomeMeu)
                payload = json.dumps(pacote)
                cliSock.sendall(payload.encode("utf-8"))


def anunciaConversa(cliSock: socket.socket, nomeMeu: str) -> None:
    print(F"Você está conversando!".center(40, "-"))
    iniciaConversa(cliSock, nomeMeu)
    print(F"Você saiu da conversa!".center(40, "-"))


def imprimeErroSeHouver(resposta: dict):
    if resposta["status"] == 400:
        print(f"Erro! {resposta['mensagem']}")


def enviaPayload(sock: socket.socket, payload: str):
    sock.sendall(payload.encode('utf-8'))

    payload_resposta = str(sock.recv(1024), encoding='utf-8')
    resposta = json.loads(payload_resposta)

    imprimeErroSeHouver(resposta)

    imprimeDebug(resposta)
    return resposta


def operacaoLogin(sock: socket.socket, username: str):
    payload = json.dumps(Login(username, PORT_LOCAL))
    return enviaPayload(sock, payload)


def operacaoLogoff(sock: socket.socket, username: str):
    payload = json.dumps(Logoff(username))
    return enviaPayload(sock, payload)


def operacaoGetLista(sock: socket.socket):
    payload = json.dumps(GetLista)
    return enviaPayload(sock, payload)


def atualizaLista(sock: socket.socket) -> dict:
    global clientes
    clientes = operacaoGetLista(sock)["clientes"]
    imprimeListaFormatada(clientes)


def conectaComOutroCliente(nomeOutro, nomeMeu):
    imprimeDebug("quero falar com alguem!")

    if(nomeOutro == nomeMeu):
        print("você não pode falar consigo mesmo!")
        return

    endrUser, portUser = clientes[nomeOutro].values()

    try:
        cliSock = iniciaCliente(endrUser, portUser)
        anunciaConversa(cliSock, nomeMeu)
    except ConnectionRefusedError:
        print(
            ERROR_RECIPIENT_DISCONECTED)


def descobreNomeRemetente(sock: socket.socket, endrOutro: str) -> str:
    atualizaLista(sock)
    print(
        list(filter(lambda dadosOutro: print(dadosOutro[1]["Endereco"], endrOutro[0], dadosOutro[1]["Porta"], endrOutro[1]), clientes.items())))
    print(
        list(filter(lambda dadosOutro: dadosOutro[1]["Endereco"] == endrOutro[0] and dadosOutro[1]["Porta"] == endrOutro[1], clientes.items())))
    return ''


def escolheNome(sock: socket.socket):
    msgUsername = "Entre com o seu username: "
    nomeMeu = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "debug" else input(
        msgUsername)
    while True:
        resposta = operacaoLogin(sock, nomeMeu)
        if(resposta["status"] == 200):
            break
        nomeMeu = input(msgUsername)
    return nomeMeu


def escolheEntrada(centralSock: socket.socket, hostSock: socket.socket, nomeMeu: str):
    while True:
        leitura, _, _ = select.select(entradas, [], [])
        for pronto in leitura:
            if pronto == hostSock:  # pedido novo de conexao
                imprimeDebug("alguem quer falar comigo!")
                cliSock, _ = aceitaConexao(hostSock)
                anunciaConversa(cliSock, nomeMeu)
            elif pronto == sys.stdin:  # entrada padrao
                comando = input()
                if comando == "logoff":
                    resposta = operacaoLogoff(centralSock, nomeMeu)
                    centralSock.close()
                    return
                elif comando == "lista":
                    pass
                elif comando in clientes:
                    conectaComOutroCliente(comando, nomeMeu)
                else:
                    print(ERROR_USER_NOT_FOUND)
            atualizaLista(centralSock)


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
