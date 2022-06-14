import sys
import socket

from cores import *

# define o tamanho em bytes do espaço alocado para receber o tamanho da mensagem
TAMANHO_MSG = 2


class Conexao:  # classe com operacoes comuns a todas as conexoes
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def recebe(self):  # recebe mensagem de uma conexao
        # recebe um tamanho fixo de bytes que vao indicar o tamanho da mensagem
        tamanho = self.sock.recv(TAMANHO_MSG)
        if not tamanho:  # dados vazios: contraparte encerrou
            return
        # recebe a quantidade de bytes recebida anteriormente indicando o tamanho total da mensagem
        conteudo = self.sock.recv(int.from_bytes(tamanho, 'big'))
        # transforma a cadeia de bytes em string e retorna
        return str(conteudo, encoding='utf-8')

    def envia(self, mensagem: str):  # envia uma mensagem a uma conexao
        # transforma a string da mensagem em cadeia de bytes
        conteudo = mensagem.encode("utf-8")
        # define o tamanho total da mensagem e converte para bytes
        tamanho = len(conteudo).to_bytes(TAMANHO_MSG, 'big')
        self.sock.sendall(tamanho)  # envia o tamanho da mensagem
        self.sock.sendall(conteudo)  # envia a mensagem

    def encerra(self):
        self.sock.close()  # encerra a conexao


# classe que define operações do lado do Servidor (tanto central quando peer)
class Servidor(Conexao):
    def __init__(self, host: str, porta: int):
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

        self.sock = sock

    def aceitaConexao(self):
        # estabelece conexao com o proximo cliente
        return self.sock.accept()


# abstracao para imprimir texto na tela
def imprime(texto: str, cor: str = COR_PADRAO, destaque: bool = False):
    colorido = cor + texto + COR_PADRAO
    print(colorido.center(60, "-") if destaque else colorido)


# abstracao para imprimir um erro (em vermelho)
def imprimeErro(texto: str):
    imprime(texto, cor=cores[0])


# imprime a lista de usuários conectados (tanto do lado do servidor central quanto do peer)
def imprimeListaFormatada(listaUsuarios: dict) -> None:
    imprime(f"Clientes conectados", destaque=True)
    if len(listaUsuarios) < 1:
        imprime("Nenhum cliente conectado!")
    for indice, (nomeOutro, infoOutro) in enumerate(listaUsuarios.items()):
        imprime(
            f"[{indice}]: {nomeOutro} {infoOutro['Endereco'],infoOutro['Porta']}")
    imprime("", destaque=True)
