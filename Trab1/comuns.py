import sys
import socket

from cores import *


class Servidor:
    def __init__(self, host: str, porta: int, entradas: list):
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

        self.sock = sock

    def encerra(self):
        self.sock.close()

    def aceitaConexao(self):
        # estabelece conexao com o proximo cliente
        return self.sock.accept()


def imprime(texto: str, cor: str = COR_PADRAO, destaque: bool = False):
    colorido = cor + texto + COR_PADRAO
    print(colorido.center(60, "-") if destaque else colorido)


def imprimeErro(texto: str):
    imprime(texto, cor=cores[0])


def imprimeDebug(msg: str) -> None:
    if (len(sys.argv) > 1 and sys.argv[1] == "debug"):
        imprime(msg)


def imprimeListaFormatada(listaUsuarios: dict) -> None:
    imprime(f"Clientes conectados", destaque=True)
    if len(listaUsuarios) < 1:
        imprime("Nenhum cliente conectado!")
    for indice, (nomeOutro, infoOutro) in enumerate(listaUsuarios.items()):
        imprime(
            f"[{indice}]: {nomeOutro} {infoOutro['Endereco'],infoOutro['Porta']}")
    imprime("", destaque=True)
