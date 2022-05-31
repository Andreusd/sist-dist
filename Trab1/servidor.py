import socket
import sys
import select
import threading
import json

from comuns import *
from payloads_servidor import *
from error_messages import *

# define a localizacao do servidor
HOST = ''  # vazio indica que podera receber requisicoes a partir de qq interface de rede da maquina
PORT = 10000  # porta de acesso

# define a lista de I/O de interesse (jah inclui a entrada padrao)
entradas = [sys.stdin]
# armazena clientes conectados e seu endereço e porta
clientes = {}

lock = threading.Lock()


def adicionaCliente(nome, dados):
    lock.acquire()
    clientes[nome] = dados
    lock.release()


def removeCliente(chave):
    lock.acquire()
    del clientes[chave]
    lock.release()


def enviaPayload(sock: socket.socket, payload: dict):
    sock.sendall(json.dumps(payload).encode('utf-8'))
    imprimeDebug(f"-> {payload}")


def operacaoLogin(clisock, conteudo, endr):
    if len(conteudo["username"]) < 3:
        enviaPayload(clisock, LoginError(
            ERROR_MIN_LENGTH))
    elif conteudo["username"] in clientes:
        enviaPayload(clisock, LoginError(
            ERROR_USERNAME_TAKEN))
    else:
        adicionaCliente(conteudo["username"], {
            "Endereco": endr[0], "Porta": conteudo["porta"]})
        enviaPayload(clisock, LoginSucess)


def operacaoLogoff(clisock, conteudo):
    if conteudo["username"] in clientes:
        removeCliente(conteudo["username"])
        enviaPayload(clisock, LogoffSucess)
    else:
        enviaPayload(clisock, LogoffError)


def operacaoGetLista(clisock):
    enviaPayload(clisock, GetListaSucess(clientes))


def identificaOperacao(clisock, conteudo, endr):
    if conteudo["operacao"] == "login":
        operacaoLogin(clisock, conteudo, endr)
    elif(conteudo["operacao"] == "logoff"):
        operacaoLogoff(clisock, conteudo)
    elif(conteudo["operacao"] == "get_lista"):
        operacaoGetLista(clisock)
    else:
        print(ERROR_INVALID_PAYLOAD)


def atendeRequisicoes(clisock: socket.socket, endr: str):
    '''Recebe mensagens e as envia de volta para o cliente (ate o cliente finalizar)
    Entrada: socket da conexao e endereco do cliente
    Saida: '''
    while True:
        # recebe dados do cliente
        data = clisock.recv(1024)

        if not data:  # dados vazios: cliente encerrou
            clisock.close()  # encerra a conexao com o cliente
            print(f"<- usuário se desconectou {endr}")
            return

        conteudo = json.loads(data)
        imprimeDebug(f"<- {conteudo}")

        identificaOperacao(clisock, conteudo, endr)


def main():
    '''Inicializa e implementa o loop principal (infinito) do servidor'''
    conexoes = []  # armazena os processos criados para fazer join
    sock = iniciaServidor(HOST, PORT, entradas)
    print("Pronto para receber conexoes...")
    while True:
        leitura, _, _ = select.select(entradas, [], [])
        for pronto in leitura:
            if pronto == sock:  # pedido novo de conexao
                clisock, endr = aceitaConexao(sock)
                print(f"-> usuário se conectou {endr}")
                # cria novo processo para atender o cliente
                cliente = threading.Thread(
                    target=atendeRequisicoes, args=(clisock, endr))
                cliente.start()
                # armazena a referencia da thread para usar com join()
                conexoes.append(cliente)
            elif pronto == sys.stdin:  # entrada padrao
                cmd = input()
                if cmd == 'exit':  # solicitacao de finalizacao do servidor
                    print('Esperando os conexoes se desconectarem...')
                    for c in conexoes:  # aguarda todos os processos terminarem
                        c.join()
                    sock.close()
                    sys.exit()
                else:
                    imprimeListaFormatada(clientes)


main()
