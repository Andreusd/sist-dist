import rpyc
from rpyc.utils.server import ThreadedServer


def novo_processo(host: str, porta: int, indice: int, vizinhos: list):
    pai = None  # o no raiz sempre tera pai '1'
    max_valor = 0  # armazena o maior valor entre os filhos
    porta_maior = None  # armazena a porta do nó com maior valor
    lider_eleito = None  # armazena o lider eleito para uso futuro da aplicação

    class Node(rpyc.Service):  # classe que implementa o RPC
        exposed_indice = indice

        def exposed_probe(self, origem):
            nonlocal pai  # referencia a variavel da funcao novo_processo
            if(pai):  # caso esse nó já tenha sido visitado anteriormente
                # origem é uma tupla em que origem[0] é o host e origem[1] a porta
                conn = rpyc.connect(origem[0], origem[1])
                # enviamos ack para informar que ja foi visitado
                conn.root.ack(porta)
                return
            pai = origem  # define o pai desse nó
            for vizinho in vizinhos:
                if vizinho != pai:  # envia probe para todos os vizinhos exceto o pai
                    print(f"-> {porta}: visita {vizinho[1]}")
                    conn = rpyc.connect(vizinho[0], vizinho[1])
                    # envia probe para os vizinhos
                    conn.root.probe((host, porta))
            if(origem != 1):  # se o nó não for a raiz, envia echo para o pai
                conn = rpyc.connect(pai[0], pai[1])
                maior_valor = max(max_valor, indice)
                # envia echo para o pai com o maior valor entre o proprio indice e o dos filhos
                conn.root.echo(porta, maior_valor,
                               porta_maior if maior_valor == max_valor else porta)
            else:
                # se o nó for raiz, notifica todos os nos do novo lider
                maior_valor = max(max_valor, indice)
                for vizinho in vizinhos:
                    conn = rpyc.connect(vizinho[0], vizinho[1])
                    conn.root.lider(
                        maior_valor, porta_maior if maior_valor == max_valor else porta)

        def exposed_ack(self, filho):
            print(f"-> {porta}: {filho} ja foi visitado anteriormente")

        def exposed_echo(self, filho, maior_valor, maior_porta):
            print(f"-> {porta}: echo {filho} com valor {maior_valor}")
            nonlocal max_valor
            max_valor = maior_valor
            nonlocal porta_maior
            porta_maior = maior_porta

        def exposed_lider(self, lider_valor, lider_porta):
            nonlocal lider_eleito
            if(lider_eleito):
                return
            lider_eleito = lider_porta
            print(
                f"-> {porta}: reconhece {lider_eleito} como lider com valor {lider_valor}")
            for vizinho in vizinhos:
                if vizinho != pai:
                    conn = rpyc.connect(vizinho[0], vizinho[1])
                    conn.root.lider(lider_valor, lider_porta)

    server = ThreadedServer(Node, hostname=host, port=porta)
    server.start()
