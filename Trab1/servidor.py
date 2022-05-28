import socket
import sys
import select
import threading
import json

from server_responses import *

# define a localizacao do servidor
HOST = ''  # vazio indica que podera receber requisicoes a partir de qq interface de rede da maquina
PORT = 10000  # porta de acesso

# define a lista de I/O de interesse (jah inclui a entrada padrao)
entradas = [sys.stdin]
# armazena historico de conexoes
clientes = {}


def iniciaServidor():
    '''Cria um socket de servidor e o coloca em modo de espera por conexoes
    Saida: o socket criado'''
    # cria o socket
    # Internet( IPv4 + TCP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # evita bug de socket already in use quando o servidor termina abruptamente
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # vincula a localizacao do servidor
    sock.bind((HOST, PORT))

    # coloca-se em modo de espera por conexoes
    sock.listen(100)

    # configura o socket para o modo nao-bloqueante
    sock.setblocking(False)

    # inclui o socket principal na lista de entradas de interesse
    entradas.append(sock)

    return sock


def aceitaConexao(sock):
    '''Aceita o pedido de conexao de um cliente
    Entrada: o socket do servidor
    Saida: o novo socket da conexao e o endereco do cliente'''

    # estabelece conexao com o proximo cliente
    clisock, endr = sock.accept()

    return clisock, endr[0]


def trataConteudo(clisock, conteudo, endr):
    if conteudo["operacao"] == "login":
        if conteudo["username"] in clientes:
            clisock.sendall(json.dumps(LOGIN_ERROR).encode('utf-8'))
        else:
            print(conteudo)
            clientes[conteudo["username"]] = {
                "Endereco": endr, "Porta": conteudo["porta"]}
            clisock.sendall(json.dumps(LOGIN_SUCCESS).encode('utf-8'))

    elif(conteudo["operacao"] == "logoff"):
        if conteudo["username"] in clientes:
            del clientes[conteudo["username"]]
            clisock.sendall(json.dumps(LOGOFF_SUCCESS).encode('utf-8'))
        else:
            clisock.sendall(json.dumps(LOGOFF_ERROR).encode('utf-8'))

    elif(conteudo["operacao"] == "get_lista"):
        clisock.sendall(json.dumps(GET_LISTA_SUCESS(clientes)).encode('utf-8'))

    else:
        pass


def atendeRequisicoes(clisock: socket.socket, endr: str):
    '''Recebe mensagens e as envia de volta para o cliente (ate o cliente finalizar)
    Entrada: socket da conexao e endereco do cliente
    Saida: '''
    while True:
        # recebe dados do cliente
        data = clisock.recv(1024)

        if not data:  # dados vazios: cliente encerrou
            clisock.close()  # encerra a conexao com o cliente
            return

        conteudo = json.loads(data)
        trataConteudo(clisock, conteudo, endr)
        print(clientes)


def main():
    '''Inicializa e implementa o loop principal (infinito) do servidor'''
    conexoes = []  # armazena os processos criados para fazer join
    sock = iniciaServidor()
    print("Pronto para receber conexoes...")
    while True:
        # espera por qualquer entrada de interesse
        leitura, _, _ = select.select(entradas, [], [])
        # tratar todas as entradas prontas
        for pronto in leitura:
            if pronto == sock:  # pedido novo de conexao
                clisock, endr = aceitaConexao(sock)
                print(endr)
                # cria novo processo para atender o cliente
                cliente = threading.Thread(
                    target=atendeRequisicoes, args=(clisock, endr))
                cliente.start()
                # armazena a referencia da thread para usar com join()
                conexoes.append(cliente)
            elif pronto == sys.stdin:  # entrada padrao
                cmd = input()
                if cmd == 'fim':  # solicitacao de finalizacao do servidor
                    print('Esperando os conexoes se desconectarem...')
                    for c in conexoes:  # aguarda todos os processos terminarem
                        c.join()
                    sock.close()
                    sys.exit()


main()
