import socket
import sys
import select
import threading
import json

from comuns import *
from payloads import *
from messages import *

# define a localizacao do servidor
HOST = ''  # vazio indica que podera receber requisicoes a partir de qq interface de rede da maquina
PORT = 10000  # porta de acesso

# armazena clientes conectados e seu endereço e porta
clientes = {}

lock = threading.Lock()


class ConexaoCliente(Conexao):
    def __init__(self, sock, endrCliente):
        super().__init__(sock)
        self.endrCliente = endrCliente

    def adicionaCliente(self, nome, dados):
        lock.acquire()
        clientes[nome] = dados
        lock.release()

    def removeCliente(self, chave):
        lock.acquire()
        del clientes[chave]
        lock.release()

    def enviaPayload(self, payload: Payload):
        self.envia(payload.toJson())
        imprimeDebug(f"-> {payload}")

    def operacaoLogin(self, conteudo):
        if len(conteudo["username"]) < 3:
            self.enviaPayload(LoginError(
                ERROR_MIN_LENGTH))
        elif conteudo["username"] in clientes:
            self.enviaPayload(LoginError(
                ERROR_USERNAME_TAKEN))
        else:
            self.adicionaCliente(conteudo["username"], {
                "Endereco": self.endrCliente[0], "Porta": conteudo["porta"]})
            self.enviaPayload(LoginSucess())

    def operacaoLogoff(self, conteudo):
        if conteudo["username"] in clientes:
            self.removeCliente(conteudo["username"])
            self.enviaPayload(LogoffSucess())
        else:
            self.enviaPayload(LogoffError())

    def operacaoGetLista(self):
        self.enviaPayload(GetListaSucess(clientes))

    def identificaOperacao(self, conteudo):
        if conteudo["operacao"] == "login":
            self.operacaoLogin(conteudo)
        elif(conteudo["operacao"] == "logoff"):
            self.operacaoLogoff(conteudo)
        elif(conteudo["operacao"] == "get_lista"):
            self.operacaoGetLista()
        else:
            imprime(ERROR_INVALID_PAYLOAD)


def atendeRequisicoes(conexaoCliente):
    while True:
        # recebe dados do cliente
        data = conexaoCliente.recebe()

        if not data:  # dados vazios: cliente encerrou
            conexaoCliente.encerra()  # encerra a conexao com o cliente
            imprime(f"<- usuário se desconectou {conexaoCliente.endrCliente}")
            return

        conteudo = json.loads(data)
        imprimeDebug(f"<- {conteudo}")

        conexaoCliente.identificaOperacao(conteudo)


def main():
    '''Inicializa e implementa o loop principal (infinito) do servidor'''
    conexoes = []  # armazena os processos criados para fazer join
    servidorCentral = Servidor(HOST, PORT)
    imprime("Pronto para receber conexoes...")
    while True:
        leitura, _, _ = select.select(
            (sys.stdin, servidorCentral.sock), (), ())
        for pronto in leitura:
            if pronto == servidorCentral.sock:  # pedido novo de conexao
                cliSock, endr = servidorCentral.aceitaConexao()
                imprime(f"-> usuário se conectou {endr}")
                # cria novo processo para atender o cliente
                conexaoCliente = ConexaoCliente(cliSock, endr)
                cliente = threading.Thread(
                    target=atendeRequisicoes, args=(conexaoCliente,))
                cliente.start()
                # armazena a referencia da thread para usar com join()
                conexoes.append(cliente)
            elif pronto == sys.stdin:  # entrada padrao
                cmd = input()
                if cmd == 'exit':  # solicitacao de finalizacao do servidor
                    imprime('Esperando os conexoes se desconectarem...')
                    for c in conexoes:  # aguarda todos os processos terminarem
                        c.join()
                    servidorCentral.encerra()
                    return
                else:
                    imprimeListaFormatada(clientes)


if __name__ == '__main__':
    main()
