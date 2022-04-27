def palavras_mais_frequentes(texto):
    contagem_palavras = {}
    for palavra in texto.replace(',', ' ').replace('.', ' ').replace('\n', ' ').split(' '):
        contagem_palavras[palavra] = contagem_palavras.get(palavra, 0) + 1
    return ' '.join(sorted(contagem_palavras.keys(), key=contagem_palavras.get, reverse=True)[:5])
