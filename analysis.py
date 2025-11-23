import os
import math
import csv
from collections import deque

from grafh_blibiotecas.adjacency_list_graph import AdjacencyListGraph
from main import ensure_data_files, load_jsons, collect_users, build_integrated_graph


def compute_degrees(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    in_deg = {v: graph.getVertexInDegree(v) for v in range(n)}
    out_deg = {v: graph.getVertexOutDegree(v) for v in range(n)}
    total = {v: in_deg[v] + out_deg[v] for v in range(n)}
    return in_deg, out_deg, total


def bfs_distances_directed(graph: AdjacencyListGraph, start: int):
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in graph._adjacency[u].keys():
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def closeness_centrality(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    closeness = {}
    for u in range(n):
        dist = bfs_distances_directed(graph, u)
        if len(dist) <= 1:
            closeness[u] = 0.0
            continue
        s = sum(dist.values())
        closeness[u] = (len(dist) - 1) / s
    return closeness


def betweenness_centrality(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    bet = {v: 0.0 for v in range(n)}
    for s in range(n):
        stack = []
        preds = {w: [] for w in range(n)}
        sigma = {w: 0.0 for w in range(n)}
        sigma[s] = 1.0
        dist = {w: -1 for w in range(n)}
        dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in graph._adjacency[v].keys():
                if dist[w] < 0:
                    q.append(w)
                    dist[w] = dist[v] + 1
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = {w: 0.0 for w in range(n)}
        while stack:
            w = stack.pop()
            for v in preds[w]:
                if sigma[w] != 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bet[w] += delta[w]
    if n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        for v in bet:
            bet[v] *= scale
    return bet


def pagerank(graph: AdjacencyListGraph, alpha=0.85, max_iter=100, tol=1.0e-6):
    n = graph.getVertexCount()
    if n == 0:
        return {}
    pr = {v: 1.0 / n for v in range(n)}
    out_deg = {v: graph.getVertexOutDegree(v) for v in range(n)}
    for _ in range(max_iter):
        new_pr = {v: (1 - alpha) / n for v in range(n)}
        for u in range(n):
            if out_deg[u] == 0:
                continue
            share = pr[u] / out_deg[u]
            for v in graph._adjacency[u].keys():
                new_pr[v] += alpha * share
        diff = sum(abs(new_pr[v] - pr[v]) for v in range(n))
        pr = new_pr
        if diff < tol:
            break
    return pr


def undirected_neighbors(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    neigh = [set() for _ in range(n)]
    for u in range(n):
        for v in graph._adjacency[u].keys():
            neigh[u].add(v)
            neigh[v].add(u)
    return neigh


def clustering_coefficients(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    neigh = undirected_neighbors(graph)
    coeff = {}
    for u in range(n):
        k = len(neigh[u])
        if k < 2:
            coeff[u] = 0.0
            continue
        neighbors_list = list(neigh[u])
        links = 0
        for i in range(k):
            v = neighbors_list[i]
            for j in range(i + 1, k):
                w = neighbors_list[j]
                if w in neigh[v]:
                    links += 1
        coeff[u] = 2 * links / (k * (k - 1))
    return coeff


def density(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    m = graph.getEdgeCount()
    if n < 2:
        return 0.0
    return m / (n * (n - 1))


def assortativity_degree(graph: AdjacencyListGraph):
    neigh = undirected_neighbors(graph)
    n = graph.getVertexCount()
    degrees = {v: graph.getVertexInDegree(v) + graph.getVertexOutDegree(v) for v in range(n)}
    xs = []
    ys = []
    seen = set()
    for u in range(n):
        for v in neigh[u]:
            if (v, u) in seen:
                continue
            seen.add((u, v))
            xs.append(degrees[u])
            ys.append(degrees[v])
    if len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / len(xs)
    var_x = sum((x - mean_x) ** 2 for x in xs) / len(xs)
    var_y = sum((y - mean_y) ** 2 for y in ys) / len(ys)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


def communities_connected_components(graph: AdjacencyListGraph):
    n = graph.getVertexCount()
    neigh = undirected_neighbors(graph)
    visited = [False] * n
    communities = []
    for v in range(n):
        if not visited[v]:
            comp = []
            stack = [v]
            visited[v] = True
            while stack:
                u = stack.pop()
                comp.append(u)
                for w in neigh[u]:
                    if not visited[w]:
                        visited[w] = True
                        stack.append(w)
            communities.append(comp)
    return communities


def top_n_pretty(title, metric, users, n=10):
    print(f"\n===== {title} (Top {n}) =====")
    print(f"{'Rank':<5} {'Usuário':<30} {'ID':<6} {'Valor':<12}")
    print("-" * 60)
    items = sorted(metric.items(), key=lambda x: x[1], reverse=True)[:n]
    for rank, (vertex, value) in enumerate(items, start=1):
        username = users[vertex]
        print(f"{rank:<5} {username:<30} {vertex:<6} {value:<12.6f}")


def export_top_n_csv(path, metric, users, n=10):
    items = sorted(metric.items(), key=lambda x: x[1], reverse=True)[:n]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["rank", "vertex_id", "username", "value"])
        for rank, (vertex, value) in enumerate(items, start=1):
            writer.writerow([rank, vertex, users[vertex], value])


def run_analysis():
    paths = ensure_data_files()
    issues, pull_requests, events = load_jsons(paths)
    users, index_by_user = collect_users(issues, pull_requests, events)
    num_vertices = len(users)
    integrated = build_integrated_graph(events, index_by_user, num_vertices)

    in_deg, out_deg, total_deg = compute_degrees(integrated)
    close = closeness_centrality(integrated)
    bet = betweenness_centrality(integrated)
    pr = pagerank(integrated)
    clust = clustering_coefficients(integrated)
    dens = density(integrated)
    assort = assortativity_degree(integrated)
    comms = communities_connected_components(integrated)

    print("Vértices:", integrated.getVertexCount())
    print("Arestas:", integrated.getEdgeCount())
    print("Densidade da rede:", dens)
    print("Assortatividade (grau):", assort)
    print("Número de comunidades (componentes):", len(comms))

    top_n_pretty("Grau total", total_deg, users)
    top_n_pretty("Betweenness", bet, users)
    top_n_pretty("Closeness", close, users)
    top_n_pretty("PageRank", pr, users)

    analysis_dir = os.path.join(os.getcwd(), "analysis")
    if not os.path.isdir(analysis_dir):
        os.makedirs(analysis_dir, exist_ok=True)

    export_top_n_csv(os.path.join(analysis_dir, "top10_degree.csv"), total_deg, users)
    export_top_n_csv(os.path.join(analysis_dir, "top10_betweenness.csv"), bet, users)
    export_top_n_csv(os.path.join(analysis_dir, "top10_closeness.csv"), close, users)
    export_top_n_csv(os.path.join(analysis_dir, "top10_pagerank.csv"), pr, users)

    summary_path = os.path.join(analysis_dir, "centrality_summary.csv")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("vertex;user;in_degree;out_degree;degree;closeness;betweenness;pagerank;clustering\n")
        for v in range(num_vertices):
            user = users[v]
            f.write(
                f"{v};{user};{in_deg[v]};{out_deg[v]};{total_deg[v]};"
                f"{close.get(v, 0.0)};{bet.get(v, 0.0)};{pr.get(v, 0.0)};{clust.get(v, 0.0)}\n"
            )
    print("\nResumo de centralidades salvo em:", summary_path)


if __name__ == "__main__":
    run_analysis()
