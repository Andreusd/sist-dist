import rpyc
from rpyc.utils.server import ThreadedServer


def novo_processo(servidor: str, porta: int, indice: int, vizinhos: list):
    origem = None  # o no raiz sempre tera raiz nula
    max_valor = 0  # armazena o maior valor entre os filhos
    porta_maior = None
    lider_eleito = None
    valor_eleito = None

    class Node(rpyc.Service):
        exposed_indice = indice

        def exposed_probe(self, orig):
            nonlocal origem  # referencia a variavel da funcao novo_processo
            if(origem):
                conn = rpyc.connect('localhost', orig)
                conn.root.ack(porta)
                return
            origem = orig
            for vizinho in vizinhos:
                if vizinho != origem:
                    print(f"-> {porta}: visita {vizinho}")
                    conn = rpyc.connect('localhost', vizinho)
                    conn.root.probe(porta)
            if(orig != 1):
                conn = rpyc.connect('localhost', origem)
                maior_valor = max(max_valor, indice)
                conn.root.echo(porta, maior_valor,
                               porta_maior if maior_valor == max_valor else porta)
            else:
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
            nonlocal valor_eleito
            if(lider_eleito):
                return
            lider_eleito = lider_porta
            valor_eleito = lider_valor
            print(
                f"-> {porta}: reconhece {lider_eleito} como lider com valor {valor_eleito}")
            for vizinho in vizinhos:
                if vizinho != origem:
                    conn = rpyc.connect('localhost', vizinho)
                    conn.root.lider(lider_valor, lider_porta)

    server = ThreadedServer(Node, hostname=servidor, port=porta)
    server.start()
