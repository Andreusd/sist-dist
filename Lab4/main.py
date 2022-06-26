import random
import multiprocessing
import random
import json
import rpyc
from node import novo_processo

MAX_INDEX = 10000

processos = []  # lista que armazena os processos que estão executando


def carrega_configuracao() -> dict:  # carrega o arquivo de configuração
    with open("configuracao.json", "r") as arquivo:
        return json.load(arquivo)


def incia_node(porta: str, dados: dict):  # inicia os nós
    # escolhe o valor armazenado por cada nó (valor comparado)
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
            # conecta com o nó que será a raiz para que ele inicie a eleição
            conn = rpyc.connect('localhost', entrada)
            conn.root.probe(1)  # probe(1) significa que o no é raiz
            break
        else:
            print("no invalido!")
    for p in processos:
        p.terminate()


if __name__ == '__main__':
    main()
