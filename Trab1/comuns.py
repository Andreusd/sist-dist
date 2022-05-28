import sys
import socket


def imprimeDebug(msg: str) -> None:
    if (len(sys.argv) > 1 and sys.argv[1] == "debug"):
        print(msg)


def imprimeListaFormatada(listaUsuarios: dict) -> None:
    print(f"Clientes conectados".center(40, "-"))
    if len(listaUsuarios) < 1:
        print("Nenhum cliente conectado!")
    for indice, (nomeOutro, infoOutro) in enumerate(listaUsuarios.items()):
        print(f"[{indice}]: {nomeOutro} {infoOutro['Endereco'],infoOutro['Porta']}")
    print(f"".center(40, "-"))


def iniciaServidor(host: str, porta: int, entradas: list) -> socket.socket:
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


def aceitaConexao(sock):
    '''Aceita o pedido de conexao de um cliente
    Entrada: o socket do servidor
    Saida: o novo socket da conexao e o endereco do cliente'''

    # estabelece conexao com o proximo cliente
    clisock, endr = sock.accept()

    return clisock, endr
