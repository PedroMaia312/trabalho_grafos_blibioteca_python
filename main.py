import os
import json
from extracao.github_extractor import GithubExtractor
from grafh_blibiotecas.adjacency_list_graph import AdjacencyListGraph

DATA_DIR = os.path.join(os.getcwd(), 'data')
ISSUES_FILE = "issues.json"
PRS_FILE = "pull_requests.json"
INTERACTIONS_FILE = "interactions.json"
EXPORT_DIR = "graphs_export"

INTEGRATED_WEIGHTS = {
    "issue_comment": 2,
    "pr_comment": 2,
    "issue_opened_commented": 3,
    "issue_closed": 3,
    "pr_review": 4,
    "pr_merge": 5,
}


def ensure_data_files():
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    paths = {
        "issues": os.path.join(DATA_DIR, ISSUES_FILE),
        "pull_requests": os.path.join(DATA_DIR, PRS_FILE),
        "interactions": os.path.join(DATA_DIR, INTERACTIONS_FILE),
    }

    all_exist = all(os.path.isfile(p) for p in paths.values())

    if all_exist:
        print("Arquivos JSON já existem, pulando etapa de extração.")
        return paths

    token = os.environ.get("TOKEN_GITHUB")
    repo = os.environ.get("GITHUB_REPO")

    if not token or not repo:
        raise RuntimeError(
            "Variáveis de ambiente TOKEN_GITHUB e GITHUB_REPO devem estar definidas para executar a extração."
        )

    print("Arquivos JSON não encontrados. Iniciando extração com GithubExtractor.")

    extractor = GithubExtractor(token, repo, output_dir=DATA_DIR)

    issues = extractor.fetch_issues(state="all")
    extractor.save_json(issues, ISSUES_FILE)

    pull_requests = extractor.fetch_pull_requests(state="all")
    extractor.save_json(pull_requests, PRS_FILE)

    interactions = extractor.build_interactions(issues, pull_requests)
    extractor.save_json(interactions, INTERACTIONS_FILE)

    return paths


def load_jsons(paths):
    with open(paths["issues"], "r", encoding="utf-8") as f:
        issues = json.load(f)
    with open(paths["pull_requests"], "r", encoding="utf-8") as f:
        pull_requests = json.load(f)
    with open(paths["interactions"], "r", encoding="utf-8") as f:
        interactions_data = json.load(f)
    events = interactions_data.get("events", [])
    return issues, pull_requests, events


def collect_users(issues, pull_requests, events):
    users = set()

    for issue in issues:
        users.add(issue.get("user"))
        closed_by = issue.get("closed_by")
        if closed_by:
            users.add(closed_by)
        for c in issue.get("comments", []):
            users.add(c.get("user"))

    for pr in pull_requests:
        users.add(pr.get("user"))
        merged_by = pr.get("merged_by")
        if merged_by:
            users.add(merged_by)
        for c in pr.get("comments", []):
            users.add(c.get("user"))
        for r in pr.get("reviews", []):
            users.add(r.get("user"))

    for e in events:
        users.add(e.get("source"))
        users.add(e.get("target"))

    users.discard(None)
    users_list = sorted(users)
    index_by_user = {u: i for i, u in enumerate(users_list)}

    print(f"Total de usuários distintos: {len(users_list)}")
    return users_list, index_by_user


def build_graph_comments(events, index_by_user, num_vertices):
    graph = AdjacencyListGraph(num_vertices)
    for e in events:
        t = e.get("type")
        if t not in ("issue_comment", "pr_comment"):
            continue
        source = e.get("source")
        target = e.get("target")
        if source not in index_by_user or target not in index_by_user:
            continue
        u = index_by_user[source]
        v = index_by_user[target]
        if u == v:
            continue
        if not graph.hasEdge(u, v):
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, 1.0)
    return graph


def build_graph_issue_closures(events, index_by_user, num_vertices):
    graph = AdjacencyListGraph(num_vertices)
    for e in events:
        if e.get("type") != "issue_closed":
            continue
        source = e.get("source")
        target = e.get("target")
        if source not in index_by_user or target not in index_by_user:
            continue
        u = index_by_user[source]
        v = index_by_user[target]
        if u == v:
            continue
        if not graph.hasEdge(u, v):
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, 1.0)
    return graph


def build_graph_reviews_merges(events, index_by_user, num_vertices):
    graph = AdjacencyListGraph(num_vertices)
    for e in events:
        t = e.get("type")
        if t not in ("pr_review", "pr_merge"):
            continue
        source = e.get("source")
        target = e.get("target")
        if source not in index_by_user or target not in index_by_user:
            continue
        u = index_by_user[source]
        v = index_by_user[target]
        if u == v:
            continue
        if not graph.hasEdge(u, v):
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, 1.0)
    return graph


def build_integrated_graph(events, index_by_user, num_vertices):
    graph = AdjacencyListGraph(num_vertices)
    for e in events:
        t = e.get("type")
        if t not in INTEGRATED_WEIGHTS:
            continue
        source = e.get("source")
        target = e.get("target")
        if source not in index_by_user or target not in index_by_user:
            continue
        u = index_by_user[source]
        v = index_by_user[target]
        if u == v:
            continue
        w = float(INTEGRATED_WEIGHTS[t])
        if not graph.hasEdge(u, v):
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, w)
        else:
            current = graph.getEdgeWeight(u, v)
            graph.setEdgeWeight(u, v, current + w)
    return graph


def export_all_graphs(graph1, graph2, graph3, integrated):
    if not os.path.isdir(EXPORT_DIR):
        os.makedirs(EXPORT_DIR, exist_ok=True)

    g1_path = os.path.join(EXPORT_DIR, "graph1_comments")
    g2_path = os.path.join(EXPORT_DIR, "graph2_issue_closures")
    g3_path = os.path.join(EXPORT_DIR, "graph3_reviews_merges")
    gi_path = os.path.join(EXPORT_DIR, "graph_integrated")

    print("Exportando Grafo 1 (comentários)...")
    graph1.exportToGEPHI(g1_path)

    print("Exportando Grafo 2 (fechamento de issues)...")
    graph2.exportToGEPHI(g2_path)

    print("Exportando Grafo 3 (reviews/merges de PR)...")
    graph3.exportToGEPHI(g3_path)

    print("Exportando Grafo Integrado...")
    integrated.exportToGEPHI(gi_path)

    print("Exportação concluída.")


def main():
    paths = ensure_data_files() #aprovada
    issues, pull_requests, events = load_jsons(paths)
    users, index_by_user = collect_users(issues, pull_requests, events)
    num_vertices = len(users)

    print("Construindo Grafo 1: comentários em issues e pull requests.")
    graph1 = build_graph_comments(events, index_by_user, num_vertices)
    print(f"Grafo 1: {graph1.getVertexCount()} vértices, {graph1.getEdgeCount()} arestas.")

    print("Construindo Grafo 2: fechamento de issues por outros usuários.")
    graph2 = build_graph_issue_closures(events, index_by_user, num_vertices)
    print(f"Grafo 2: {graph2.getVertexCount()} vértices, {graph2.getEdgeCount()} arestas.")

    print("Construindo Grafo 3: revisões/aprovações/merges de pull requests.")
    graph3 = build_graph_reviews_merges(events, index_by_user, num_vertices)
    print(f"Grafo 3: {graph3.getVertexCount()} vértices, {graph3.getEdgeCount()} arestas.")

    print("Construindo Grafo Integrado ponderado.")
    integrated = build_integrated_graph(events, index_by_user, num_vertices)
    print(f"Grafo Integrado: {integrated.getVertexCount()} vértices, {integrated.getEdgeCount()} arestas.")

    export_all_graphs(graph1, graph2, graph3, integrated)


if __name__ == "__main__":
    main()
