import rpyc
from rpyc.utils.server import ThreadedServer


def novo_processo(servidor: str, porta: int, indice: int, vizinhos: list):
    pai = None  # o no raiz sempre tera pai '1'
    max_valor = 0  # armazena o maior valor entre os filhos
    porta_maior = None  # armazena a porta do nó com maior valor
    lider_eleito = None  # armazena o lider eleito para uso futuro da aplicação

    class Node(rpyc.Service):  # classe que implementa o RPC
        exposed_indice = indice

        def exposed_probe(self, origem):
            nonlocal pai  # referencia a variavel da funcao novo_processo
            if(pai):  # caso esse nó já tenha sido visitado anteriormente
                conn = rpyc.connect('localhost', origem)
                # enviamos ack para informar que ja foi visitado
                conn.root.ack(porta)
                return
            pai = origem  # define o pai desse nó
            for vizinho in vizinhos:
                if vizinho != pai:  # envia probe para todos os vizinhos exceto o pai
                    print(f"-> {porta}: visita {vizinho}")
                    conn = rpyc.connect('localhost', vizinho)
                    conn.root.probe(porta)  # envia probe para os vizinhos
            if(origem != 1):  # se o nó não for a raiz, envia echo para o pai
                conn = rpyc.connect('localhost', pai)
                maior_valor = max(max_valor, indice)
                # envia echo para o pai com o maior valor entre o proprio indice e o dos filhos
                conn.root.echo(porta, maior_valor,
                               porta_maior if maior_valor == max_valor else porta)
            else:
                # se o nó for raiz, notifica todos os nos do novo lider
                maior_valor = max(max_valor, indice)
                for vizinho in vizinhos:
                    conn = rpyc.connect('localhost', vizinho)
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
                    conn = rpyc.connect('localhost', vizinho)
                    conn.root.lider(lider_valor, lider_porta)

    server = ThreadedServer(Node, hostname=servidor, port=porta)
    server.start()
