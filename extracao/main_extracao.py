import os
import json
from typing import Any
from dotenv import load_dotenv
from github_extractor import GithubExtractor


def salvar_json(self, data: Any, filename: str) -> str:
    path = os.path.join(self.output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Arquivo salvo em: {path}")
    return path


if __name__ == "__main__":
    load_dotenv()

    token = os.environ.get("TOKEN_GITHUB")
    repo = os.environ.get("GITHUB_REPO", "boto/boto3")
    output_dir = os.environ.get("OUTPUT_DIR", "data")

    if not token:
        raise RuntimeError("Variável de ambiente TOKEN_GITHUB não definida")

    extractor = GithubExtractor(token, repo, output_dir=output_dir)

    issues = extractor.fetch_issues(state="all")
    salvar_json(issues, "issues.json")

    pull_requests = extractor.fetch_pull_requests(state="all")
    salvar_json(pull_requests, "pull_requests.json")

    interacoes = extractor.build_interacoes(issues, pull_requests)
    salvar_json(interacoes, "interacoes.json")

    print("Tudo foi extraido com sucesso!")