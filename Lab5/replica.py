import json
import sys
import os
import rpyc
from rpyc.utils.server import ThreadedServer
import threading

DEBUG = True

identificador = None
configuracao = None
valor_X = 0
historico = []
dono_token = '1'


def imprime_debug(mensagem):
    if DEBUG:
        print(mensagem)


def carrega_configuracao() -> dict:
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


def inicia_rpyc():
    class Node(rpyc.Service):
        def exposed_pega_token(self, remetente):
            global dono_token
            dono_token = remetente
            imprime_debug(
                f"{identificador} -> O novo dono do token e {dono_token}")
            for vizinho in configuracao:
                if vizinho != identificador:
                    conn = rpyc.connect(
                        configuracao[vizinho]['host'], configuracao[vizinho]['porta'])
                    conn.root.define_novo_dono(remetente)

        def exposed_define_novo_dono(self, remetente):
            global dono_token
            dono_token = remetente
            imprime_debug(
                f"{identificador} -> O novo dono do token e {dono_token}")

        def exposed_atualiza_X(self, remetente, valor):
            global valor_X
            valor_X = valor
            imprime_debug(f"{identificador} -> O novo valor de X e {valor_X}")
            conn = rpyc.connect(
                configuracao[remetente]['host'], configuracao[remetente]['porta'])
            conn.root.reconhece_X(identificador, valor)

        def exposed_reconhece_X(self, remetente, valor):
            imprime_debug(
                f"{identificador} -> O par {remetente} reconhece {valor} como o novo valor de X")
    node = ThreadedServer(Node, port=configuracao[identificador]['porta'])
    threading.Thread(target=node.start).start()


def atualiza_valor(valores):
    if dono_token != identificador:
        conn = rpyc.connect(
            configuracao[dono_token]['host'], configuracao[dono_token]['porta'])
        conn.root.pega_token(identificador)
    if dono_token == identificador:
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
    inicia_rpyc()
    try:
        atende_requisicoes()
    except Exception as e:
        print(
            f"Erro ao conectar com um dos pares, provavelmente ele nao esta executando: {str(e)}")
        os._exit(0)


if __name__ == '__main__':
    main()
