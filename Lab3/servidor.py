# servidor de echo: lado servidor
# com finalizacao do lado do servidor
# com multiprocesso
import socket
import select
import sys
import multiprocessing

from funcoes import palavras_mais_frequentes

# define a localizacao do servidor
HOST = ''  # vazio indica que podera receber requisicoes a partir de qq interface de rede da maquina
PORT = 10001  # porta de acesso

# define a lista de I/O de interesse (jah inclui a entrada padrao)
entradas = [sys.stdin]
# armazena historico de conexoes
conexoes = {}


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
    sock.listen(5)

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

    # registra a nova conexao
    conexoes[clisock] = endr

    return clisock, endr


def atendeRequisicoes(clisock, endr):
    '''Recebe mensagens e as envia de volta para o cliente (ate o cliente finalizar)
    Entrada: socket da conexao e endereco do cliente
    Saida: '''

    while True:
        # recebe dados do cliente
        data = clisock.recv(1024)

        if not data:  # dados vazios: cliente encerrou
            print(str(endr) + '-> encerrou')
            clisock.close()  # encerra a conexao com o cliente
            return

        try:
            # tenta abrir o arquivo com o nome que o cliente forneceu
            with open(file=str(data, encoding='utf-8'), mode='r', encoding='utf-8') as arquivo:
                texto = arquivo.read()
            # envia o conteudo do arquivo tratado para o cliente
            clisock.send(palavras_mais_frequentes(texto).encode())
        # captura a excessao quando nao acha o arquivo
        except FileNotFoundError:
            clisock.send(b"Erro: o arquivo nao foi encontrado")

        print(str(endr) + ': ' + str(data, encoding='utf-8'))


def main():
    '''Inicializa e implementa o loop principal (infinito) do servidor'''
    clientes = []  # armazena os processos criados para fazer join
    sock = iniciaServidor()
    print("Pronto para receber conexoes...")
    while True:
        # espera por qualquer entrada de interesse
        leitura, escrita, excecao = select.select(entradas, [], [])
        # tratar todas as entradas prontas
        for pronto in leitura:
            if pronto == sock:  # pedido novo de conexao
                clisock, endr = aceitaConexao(sock)
                print('Conectado com: ', endr)
                # cria novo processo para atender o cliente
                cliente = multiprocessing.Process(
                    target=atendeRequisicoes, args=(clisock, endr))
                cliente.start()
                # armazena a referencia da thread para usar com join()
                clientes.append(cliente)
            elif pronto == sys.stdin:  # entrada padrao
                cmd = input()
                if cmd == 'fim':  # solicitacao de finalizacao do servidor
                    print('Esperando os clientes se desconectarem...')
                    for c in clientes:  # aguarda todos os processos terminarem
                        c.join()
                    sock.close()
                    sys.exit()
                elif cmd == 'hist':  # outro exemplo de comando para o servidor
                    print(str(conexoes.values()))


main()
