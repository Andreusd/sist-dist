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
        configuracao: dict = json.load(arquivo)
    for node in configuracao.values():
        # transforma a configuração de forma a deixar exposto o host e porta de cada node vizinho
        node["vizinhos"] = list(map(lambda vizinho: (
            configuracao[vizinho]["host"], vizinho), node["vizinhos"]))
    return configuracao


def incia_node(porta: str, dados: dict):  # inicia os nós
    # escolhe o valor armazenado por cada nó (valor comparado)
    valor = random.randrange(MAX_INDEX)
    vizinhos_formatado = ", ".join(
        map(lambda viz: f"{viz[1]}({viz[0]})", dados['vizinhos']))
    print(
        f"-> Iniciando node {porta}({dados['host']}) com vizinhos {vizinhos_formatado} com valor {valor}")
    processo = multiprocessing.Process(target=novo_processo, args=(
        dados['host'], porta, valor, dados['vizinhos']))
    processo.start()
    processos.append(processo)


def main():
    nodes = carrega_configuracao()
    for indice, dados in nodes.items():
        incia_node(indice, dados)
    print("Entre com a porta do node que vai iniciar a eleicao (ex: 5000)")
    entrada = None
    while True:
        entrada = input()
        if entrada in nodes:
            # conecta com o nó que será a raiz para que ele inicie a eleição
            conn = rpyc.connect(nodes[entrada]['host'], entrada)
            conn.root.probe(1)  # probe(1) significa que o no é raiz
            break
        else:
            print("no invalido!")
    for p in processos:
        p.terminate()


if __name__ == '__main__':
    main()
