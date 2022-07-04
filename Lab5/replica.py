import json
import sys
import os
import rpyc
from rpyc.utils.server import ThreadedServer
import threading

DEBUG = True  # ativa modo de debug

identificador = None  # identificador do proprio no
configuracao = None  # estrutura com os endereco dos pares
valor_X = 0  # valor local da variavel X
historico = []  # historico local de atualizacao da variavel X
dono_token = '1'  # armazena o dono do token (padrao = 1)


def imprime_debug(mensagem):
    if DEBUG:
        print(mensagem)


def carrega_configuracao() -> dict:  # funcao que carrega a configuracao do arquivo
    with open('configuracao.json', 'r') as arquivo:
        return json.load(arquivo)


def inicia():
    global identificador
    global configuracao
    if len(sys.argv) < 2:
        print(f"-> Digite {sys.argv[0]} <identificador da thread>")
        sys.exit(1)
    identificador = sys.argv[1]
    configuracao = carrega_configuracao()
    if identificador not in configuracao:
        print(
            f"-> Identificador {identificador} deve pertencer ao intervalo [1..4]")
        sys.exit(1)
    print('''
    Bem vinda, digite ler para ler o valor atual de X na réplica,
    Digite historico para ler o historico de alteracoes do valor de X,
    Digite alterar <valor1> <valor2> <valor3>... para alterar o valor de X
    Digite sair para sair
    ''')


def inicia_rpc():  # inicia a porta para os pares se conectarem
    class Node(rpyc.Service):  # classe que implementa o rpc
        # funcao que solicita o token para o dono do token
        def exposed_pega_token(self, remetente):
            global dono_token
            dono_token = remetente
            imprime_debug(
                f"{identificador} -> O novo dono do token e {dono_token}")
            # avisa a todos sobre o novo dono (inclusive o proprio novo dono)
            for vizinho in configuracao:
                if vizinho != identificador:  # para evitar uma conexao desnecessaria ja defini o novo dono anteriormente
                    conn = rpyc.connect(
                        configuracao[vizinho]['host'], configuracao[vizinho]['porta'])  # conecta com o vizinho
                    # avisa a todos sobre o novo dono
                    conn.root.define_novo_dono(remetente)

        # funcao que avisa a todos sobre o novo dono
        def exposed_define_novo_dono(self, remetente):
            global dono_token
            dono_token = remetente
            imprime_debug(
                f"{identificador} -> O novo dono do token e {dono_token}")

        # funcao que atualiza o valor da variavel X apos ela ser atualizada na copia primaria
        def exposed_atualiza_X(self, remetente, valor):
            global valor_X
            valor_X = valor
            imprime_debug(f"{identificador} -> O novo valor de X e {valor_X}")
            conn = rpyc.connect(
                configuracao[remetente]['host'], configuracao[remetente]['porta'])
            # callback para a copia primaria avisando que o valor foi atualizado com sucesso
            conn.root.reconhece_X(identificador, valor)

        # funcao ativada pelo callback
        def exposed_reconhece_X(self, remetente, valor):
            imprime_debug(
                f"{identificador} -> O par {remetente} reconhece {valor} como o novo valor de X")

    node = ThreadedServer(Node, port=configuracao[identificador]['porta'])
    threading.Thread(target=node.start).start()


def atualiza_valor(valores):  # escreve sequencialmente valores na variavel X
    # converte os valores digitados para inteiros
    valores = [int(valor) for valor in valores]
    if dono_token != identificador:
        conn = rpyc.connect(
            configuracao[dono_token]['host'], configuracao[dono_token]['porta'])
        # solicita a posse do token para o dono
        conn.root.pega_token(identificador)
    if dono_token == identificador:  # verifica se o token pertence ao proprio
        global valor_X
        global historico
        for valor in valores:
            valor_X = valor
            historico.append((identificador, valor))
        print(f"O valor de X foi atualizado para {valor_X}")
        for vizinho in configuracao:
            if vizinho != identificador:
                conn = rpyc.connect(
                    configuracao[vizinho]['host'], configuracao[vizinho]['porta'])
                # publica o valor de X para os vizinhos
                conn.root.atualiza_X(identificador, valor_X)


def atende_requisicoes():
    while True:
        cmd = input()
        lexemas = cmd.split(' ')
        if lexemas[0] == 'ler':
            print(f'X: {valor_X}')
        elif lexemas[0] == 'historico':
            print(f'Historico: {historico}')
        elif lexemas[0] == 'alterar':
            atualiza_valor(lexemas[1:])
        elif lexemas[0] == 'sair':
            os._exit(0)
        else:
            print('comando nao reconhecido')


def main():
    inicia()
    inicia_rpc()
    try:
        atende_requisicoes()
    except Exception as e:
        print(
            f"Erro ao conectar com um dos pares, provavelmente ele nao esta executando: {str(e)}")
        os._exit(0)


if __name__ == '__main__':
    main()
