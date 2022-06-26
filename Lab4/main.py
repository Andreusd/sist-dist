import random
import multiprocessing
import random
import json
import rpyc
from node import novo_processo

MAX_INDEX = 10000

processos = []


def carrega_configuracao() -> dict:
    with open("configuracao.json", "r") as arquivo:
        return json.load(arquivo)


def incia_node(porta: str, dados: dict):
    valor = random.randrange(MAX_INDEX)
    print(
        f"-> Iniciando node {porta} com vizinhos {dados['vizinhos']} no {dados['servidor']} com valor {valor}")
    processo = multiprocessing.Process(target=novo_processo, args=(
        dados['servidor'], porta, valor, dados['vizinhos']))
    processo.start()
    processos.append(processo)


def main():
    nodes = carrega_configuracao()
    for indice, dados in nodes.items():
        incia_node(indice, dados)
    print("entre com o identificador do no que vai iniciar a eleicao")
    entrada = None
    while True:
        entrada = input()
        if entrada in nodes.keys():
            conn = rpyc.connect('localhost', entrada)
            conn.root.probe(1)  # probe(1) significa que o no é raiz
            break
        else:
            print("no invalido!")
    for p in processos:
        p.terminate()
    print("terminei")


if __name__ == '__main__':
    main()
