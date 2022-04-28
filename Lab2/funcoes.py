import re


def palavras_mais_frequentes(texto):
    contagem_palavras = {}
    # trata o conteudo do arquivo, removendo espacos e quebra de linha
    for palavra in re.sub('( +)', ' ', texto.replace('\n', ' ').replace('.', ' ').replace(',', ' ')).split(' '):
        # conta as ocorrencias de uma palavra
        contagem_palavras[palavra] = contagem_palavras.get(palavra, 0) + 1
    # ordena a lista de acordo com o numero de ocorrencias da palavra e junta essa lista em uma string
    return ' '.join(sorted(contagem_palavras.keys(), key=contagem_palavras.get, reverse=True)[:5])
