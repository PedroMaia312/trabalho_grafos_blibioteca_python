import os
import math
import csv
from collections import deque

from grafh_blibiotecas.adjacency_list_graph import AdjacencyListGraph
from main import ensure_data_files, load_jsons, collect_users, build_integrated_graph


def compute_degrees(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    graus_entrada = {vertice: graph.getVertexInDegree(vertice) for vertice in range(numero_vertices)}
    graus_saida = {vertice: graph.getVertexOutDegree(vertice) for vertice in range(numero_vertices)}
    graus_total = {vertice: graus_entrada[vertice] + graus_saida[vertice] for vertice in range(numero_vertices)}
    return graus_entrada, graus_saida, graus_total


def bfs_distances_directed(graph: AdjacencyListGraph, vertice_inicial: int):
    distancias = {vertice_inicial: 0}
    fila = deque([vertice_inicial])
    while fila:
        vertice_atual = fila.popleft()
        for vizinho in graph._adjacency[vertice_atual].keys():
            if vizinho not in distancias:
                distancias[vizinho] = distancias[vertice_atual] + 1
                fila.append(vizinho)
                
    return distancias


def closeness_centrality(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    centralidade = {}
    
    for vertice_atual in range(numero_vertices):
        distancias = bfs_distances_directed(graph, vertice_atual) 
        if len(distancias) <= 1:
            centralidade[vertice_atual] = 0.0
            continue 
        soma_distancias = sum(distancias.values())
        centralidade[vertice_atual] = (len(distancias) - 1) / soma_distancias
        
    return centralidade


def betweenness_centrality(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    centralidade = {i: 0.0 for i in range(numero_vertices)}
    
    for origem in range(numero_vertices):
        pilha = []
        predecessores = {i: [] for i in range(numero_vertices)}
        
        contagem_caminhos = {i: 0.0 for i in range(numero_vertices)}
        contagem_caminhos[origem] = 1.0
        
        distancias = {i: -1 for i in range(numero_vertices)}
        distancias[origem] = 0
        
        fila = deque([origem])
        
        while fila:
            vertice_atual = fila.popleft()
            pilha.append(vertice_atual)
            
            for vizinho in graph._adjacency[vertice_atual].keys():
                if distancias[vizinho] < 0:
                    fila.append(vizinho)
                    distancias[vizinho] = distancias[vertice_atual] + 1
                
                if distancias[vizinho] == distancias[vertice_atual] + 1:
                    contagem_caminhos[vizinho] += contagem_caminhos[vertice_atual]
                    predecessores[vizinho].append(vertice_atual)
        
        dependencia = {i: 0.0 for i in range(numero_vertices)}
        
        while pilha:
            vertice_pilha = pilha.pop()
            
            for predecessor in predecessores[vertice_pilha]:
                if contagem_caminhos[vertice_pilha] != 0:
                    peso = (contagem_caminhos[predecessor] / contagem_caminhos[vertice_pilha])
                    dependencia[predecessor] += peso * (1 + dependencia[vertice_pilha])
            
            if vertice_pilha != origem:
                centralidade[vertice_pilha] += dependencia[vertice_pilha]
                
    if numero_vertices > 2:
        escala = 1.0 / ((numero_vertices - 1) * (numero_vertices - 2))
        for v in centralidade:
            centralidade[v] *= escala
            
    return centralidade


def pagerank(graph: AdjacencyListGraph, alpha=0.85, max_iter=100, tol=1.0e-6):
    numero_vertices = graph.getVertexCount()
    
    if numero_vertices == 0:
        return {}
        
    pagerank_atual = {i: 1.0 / numero_vertices for i in range(numero_vertices)}
    
    graus_saida = {i: graph.getVertexOutDegree(i) for i in range(numero_vertices)}
    
    for _ in range(max_iter):
        valor_base = (1 - alpha) / numero_vertices
        novo_pagerank = {i: valor_base for i in range(numero_vertices)}
        
        for vertice_origem in range(numero_vertices):
            if graus_saida[vertice_origem] == 0:
                continue
            
            valor_compartilhado = pagerank_atual[vertice_origem] / graus_saida[vertice_origem]
            
            for vizinho in graph._adjacency[vertice_origem].keys():
                novo_pagerank[vizinho] += alpha * valor_compartilhado
                
        diferenca_total = sum(abs(novo_pagerank[i] - pagerank_atual[i]) for i in range(numero_vertices))
        
        pagerank_atual = novo_pagerank
        
        if diferenca_total < tol:
            break
            
    return pagerank_atual


def undirected_neighbors(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    
    vizinhos_nao_direcionados = [set() for _ in range(numero_vertices)]
    
    for vertice_origem in range(numero_vertices):
        for vertice_destino in graph._adjacency[vertice_origem].keys():
            vizinhos_nao_direcionados[vertice_origem].add(vertice_destino)
            vizinhos_nao_direcionados[vertice_destino].add(vertice_origem)
            
    return vizinhos_nao_direcionados


def clustering_coefficients(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    
    vizinhos_por_vertice = undirected_neighbors(graph)
    
    coeficientes = {}
    
    for vertice_atual in range(numero_vertices):
        quantidade_vizinhos = len(vizinhos_por_vertice[vertice_atual])
        
        if quantidade_vizinhos < 2:
            coeficientes[vertice_atual] = 0.0
            continue
            
        lista_de_vizinhos = list(vizinhos_por_vertice[vertice_atual])
        conexoes_entre_vizinhos = 0
        
        for i in range(quantidade_vizinhos):
            vizinho_um = lista_de_vizinhos[i]
            
            for j in range(i + 1, quantidade_vizinhos):
                vizinho_dois = lista_de_vizinhos[j]
                
                if vizinho_dois in vizinhos_por_vertice[vizinho_um]:
                    conexoes_entre_vizinhos += 1
                    
        coeficientes[vertice_atual] = 2 * conexoes_entre_vizinhos / (quantidade_vizinhos * (quantidade_vizinhos - 1))
        
    return coeficientes


def density(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    numero_arestas = graph.getEdgeCount()
    
    if numero_vertices < 2:
        return 0.0     
    return numero_arestas / (numero_vertices * (numero_vertices - 1))


def assortativity_degree(graph: AdjacencyListGraph):
    vizinhos = undirected_neighbors(graph)
    numero_vertices = graph.getVertexCount()
    
    graus_totais = {v: graph.getVertexInDegree(v) + graph.getVertexOutDegree(v) for v in range(numero_vertices)}
    
    lista_graus_x = []
    lista_graus_y = []
    arestas_visitadas = set()
    
    for vertice_u in range(numero_vertices):
        for vertice_v in vizinhos[vertice_u]:
            if (vertice_v, vertice_u) in arestas_visitadas:
                continue
                
            arestas_visitadas.add((vertice_u, vertice_v))
            
            lista_graus_x.append(graus_totais[vertice_u])
            lista_graus_y.append(graus_totais[vertice_v])
            
    if len(lista_graus_x) < 2:
        return 0.0
        
    media_x = sum(lista_graus_x) / len(lista_graus_x)
    media_y = sum(lista_graus_y) / len(lista_graus_y)
    
    soma_covariancia = sum((x - media_x) * (y - media_y) for x, y in zip(lista_graus_x, lista_graus_y))
    covariancia = soma_covariancia / len(lista_graus_x)
    
    soma_diff_x = sum((x - media_x) ** 2 for x in lista_graus_x)
    variancia_x = soma_diff_x / len(lista_graus_x)
    
    soma_diff_y = sum((y - media_y) ** 2 for y in lista_graus_y)
    variancia_y = soma_diff_y / len(lista_graus_y)
    
    if variancia_x == 0 or variancia_y == 0:
        return 0.0
        
    return covariancia / math.sqrt(variancia_x * variancia_y)


def communities_connected_components(graph: AdjacencyListGraph):
    numero_vertices = graph.getVertexCount()
    vizinhos_por_vertice = undirected_neighbors(graph)
    
    visitados = [False] * numero_vertices
    comunidades = []
    
    for vertice_atual in range(numero_vertices):
        if not visitados[vertice_atual]:
            componente_atual = []
            pilha = [vertice_atual]
            visitados[vertice_atual] = True
            
            while pilha:
                vertice_visitado = pilha.pop()
                componente_atual.append(vertice_visitado)
                
                for vizinho in vizinhos_por_vertice[vertice_visitado]:
                    if not visitados[vizinho]:
                        visitados[vizinho] = True
                        pilha.append(vizinho)
                        
            comunidades.append(componente_atual)
            
    return comunidades


def top_n_pretty(titulo, metrica, usuarios, quantidade=10):
    print(f"\n===== {titulo} (Top {quantidade}) =====")
    print(f"{'Rank':<5} {'Usuário':<30} {'ID':<6} {'Valor':<12}")
    print("-" * 60)
    itens_ordenados = sorted(metrica.items(), key=lambda item: item[1], reverse=True)[:quantidade]
    for posicao, (id_vertice, valor) in enumerate(itens_ordenados, start=1):
        nome_usuario = usuarios[id_vertice]
        print(f"{posicao:<5} {nome_usuario:<30} {id_vertice:<6} {valor:<12.6f}")


def export_top_n_csv(caminho_arquivo, dados_metrica, lista_usuarios, quantidade=10):
    itens_ordenados = sorted(dados_metrica.items(), key=lambda item: item[1], reverse=True)[:quantidade]
    
    with open(caminho_arquivo, "w", newline="", encoding="utf-8") as arquivo_saida:
        escritor_csv = csv.writer(arquivo_saida, delimiter=";")
        
        escritor_csv.writerow(["rank", "vertex_id", "username", "value"])
        
        for posicao, (id_vertice, valor) in enumerate(itens_ordenados, start=1):
            escritor_csv.writerow([posicao, id_vertice, lista_usuarios[id_vertice], valor])


def run_analysis():
    caminhos_arquivos = ensure_data_files()
    dados_issues, dados_prs, dados_eventos = load_jsons(caminhos_arquivos)
    
    lista_usuarios, mapa_usuario_indice = collect_users(dados_issues, dados_prs, dados_eventos)
    numero_total_vertices = len(lista_usuarios)
    
    grafo_integrado = build_integrated_graph(dados_eventos, mapa_usuario_indice, numero_total_vertices)

    graus_entrada, graus_saida, graus_total = compute_degrees(grafo_integrado)
    centralidade_closeness = closeness_centrality(grafo_integrado)
    centralidade_betweenness = betweenness_centrality(grafo_integrado)
    resultado_pagerank = pagerank(grafo_integrado)
    coeficientes_agrupamento = clustering_coefficients(grafo_integrado)
    densidade_rede = density(grafo_integrado)
    assortatividade = assortativity_degree(grafo_integrado)
    comunidades_detectadas = communities_connected_components(grafo_integrado)

    agrupamento_medio = sum(coeficientes_agrupamento.values()) / numero_total_vertices if numero_total_vertices > 0 else 0.0

    print("Vértices:", grafo_integrado.getVertexCount())
    print("Arestas:", grafo_integrado.getEdgeCount())
    print("Densidade da rede:", densidade_rede)
    print("Assortatividade (grau):", assortatividade)
    print("Número de comunidades (componentes):", len(comunidades_detectadas))
    print("Clustering médio:", agrupamento_medio)

    top_n_pretty("Grau total", graus_total, lista_usuarios)
    top_n_pretty("Betweenness", centralidade_betweenness, lista_usuarios)
    top_n_pretty("Closeness", centralidade_closeness, lista_usuarios)
    top_n_pretty("PageRank", resultado_pagerank, lista_usuarios)
    top_n_pretty("Clustering Coefficient", coeficientes_agrupamento, lista_usuarios)

    diretorio_analise = os.path.join(os.getcwd(), "analysis")
    if not os.path.isdir(diretorio_analise):
        os.makedirs(diretorio_analise, exist_ok=True)

    export_top_n_csv(os.path.join(diretorio_analise, "top10_degree.csv"), graus_total, lista_usuarios)
    export_top_n_csv(os.path.join(diretorio_analise, "top10_betweenness.csv"), centralidade_betweenness, lista_usuarios)
    export_top_n_csv(os.path.join(diretorio_analise, "top10_closeness.csv"), centralidade_closeness, lista_usuarios)
    export_top_n_csv(os.path.join(diretorio_analise, "top10_pagerank.csv"), resultado_pagerank, lista_usuarios)
    export_top_n_csv(os.path.join(diretorio_analise, "top10_clustering.csv"), coeficientes_agrupamento, lista_usuarios)

    caminho_resumo = os.path.join(diretorio_analise, "centrality_summary.csv")
    with open(caminho_resumo, "w", encoding="utf-8") as arquivo_resumo:
        arquivo_resumo.write("vertex;user;in_degree;out_degree;degree;closeness;betweenness;pagerank;clustering\n")
        
        for id_vertice in range(numero_total_vertices):
            nome_usuario = lista_usuarios[id_vertice]
            
            linha = (
                f"{id_vertice};{nome_usuario};"
                f"{graus_entrada[id_vertice]};{graus_saida[id_vertice]};{graus_total[id_vertice]};"
                f"{centralidade_closeness.get(id_vertice, 0.0)};"
                f"{centralidade_betweenness.get(id_vertice, 0.0)};"
                f"{resultado_pagerank.get(id_vertice, 0.0)};"
                f"{coeficientes_agrupamento.get(id_vertice, 0.0)}\n"
            )
            arquivo_resumo.write(linha)
            
    print("\nResumo de centralidades salvo em:", caminho_resumo)


if __name__ == "__main__":
    run_analysis()