import json

import requests
from bs4 import BeautifulSoup


def get_conteudo_documentacao(links_file):
    # Carrega o arquivo com os links e retorna uma lista
    with open(links_file, 'r') as file:
        links = set(file.readlines())
    conteudo_documentacoes = []

    for link in links:
        link = link.strip()  # Limpa a URL, se necessário
        print(link)
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Localiza o elemento que contém o conteúdo do artigo
            conteudo_documentacoes_divs = soup.find_all('div', class_='content')
            print(conteudo_documentacoes_divs)
            if conteudo_documentacoes_divs:
                conteudo = ""
                for div in conteudo_documentacoes_divs:
                    paragrafos = div.find_all('p')
                    # Concatena o texto de todos os parágrafos encontrados em cada div
                    conteudo += ' ' + ' '.join(p.get_text(strip=True) for p in paragrafos)
                conteudo_documentacoes.append(conteudo.strip())
                print(conteudo)
            else:
                conteudo_documentacoes.append("Conteúdo não encontrado.")
        else:
            conteudo_documentacoes.append(f"Falha ao extrair o conteúdo da documentação): {response.status_code}")

    # Salva o conteúdo em um arquivo JSON
    with open('documentacao_stride.json', 'w') as json_file:
        json.dump({"documentacao_stride": conteudo_documentacoes}, json_file)


# Chamada da função para extrair os conteúdos
get_conteudo_documentacao('urls_documentacao_stride.txt')
