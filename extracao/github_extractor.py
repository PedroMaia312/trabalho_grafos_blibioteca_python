from github import Github, Repository
from typing import Any
import os
import json


class GithubExtractor:
    def __init__(self, github_token: str, repositorio: str, output_dir: str = "data"):
        try:
            self.conta_git = Github(github_token)
            self.repo: Repository = self.conta_git.get_repo(repositorio)
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"Conexão estabelecida com sucesso ao repositório: {self.repo.full_name}")
        except Exception as e:
            raise Exception(f"Erro ao conectar ao GitHub ou carregar o repositório: {e}")


    def _username(self, user) -> str:
        return getattr(user, "login", None)


    def _formatar_data(self, dt) -> str:
        try:
            return dt.isoformat()
        except Exception:
            return str(dt)
        

    def save_json(self, data: Any, filename: str) -> str:
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Arquivo salvo em: {path}")
        return path


    def fetch_issues(self) -> list[dict[str, Any]]:
        issues_data = []
        print("Buscando issues...")
        cont = 0
        for issue in self.repo.get_issues(state="all"):
            if getattr(issue, "pull_request", None) is not None:
                continue

            issue_dict = {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "user": self._username(issue.user),
                "state": issue.state,
                "created_at": self._formatar_data(issue.created_at),
                "closed_at": self._formatar_data(issue.closed_at),
                "closed_by": self._username(getattr(issue, "closed_by", None)),
                "comments": []
            }

            comments_data = []
            for comment in issue.get_comments():
                comments_data.append(
                    {
                        "user": self._username(comment.user),
                        "created_at": self._formatar_data(comment.created_at),
                        "body": comment.body
                    }
                )
            issue_dict["comments"] = comments_data
            issues_data.append(issue_dict)
            cont += 1
            print(cont)
            print(f"Usuario: {issue_dict['user']} Titulo: {issue_dict['title']}")

        print(f"Total de issues coletadas: {len(issues_data)}")
        return issues_data


    def fetch_pull_requests(self) -> list[dict[str, Any]]:
        prs_data = []
        print("Buscando pull requests...")
        cont = 0
        for pr in self.repo.get_pulls(state="all"):
            pr_dict = {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "user": self._username(pr.user),
                "state": pr.state,
                "created_at": self._formatar_data(pr.created_at),
                "closed_at": self._formatar_data(pr.closed_at),
                "merged": pr.merged,
                "merged_at": self._formatar_data(pr.merged_at),
                "merged_by": self._username(pr.merged_by),
                "comments": [],
                "reviews": []
            }

            issue_comments = []
            for comment in pr.get_issue_comments():
                issue_comments.append(
                    {
                        "user": self._username(comment.user),
                        "created_at": self._formatar_data(comment.created_at),
                        "body": comment.body
                    }
                )

            review_comments = []
            for comment in pr.get_comments():
                review_comments.append(
                    {
                        "user": self._username(comment.user),
                        "created_at": self._formatar_data(comment.created_at),
                        "body": comment.body,
                        "path": getattr(comment, "path", None)
                    }
                )

            pr_dict["comments"] = issue_comments + review_comments

            reviews_data = []
            for review in pr.get_reviews():
                reviews_data.append(
                    {
                        "user": self._username(review.user),
                        "state": review.state,
                        "submitted_at": self._formatar_data(review.submitted_at),
                        "body": review.body
                    }
                )

            pr_dict["reviews"] = reviews_data
            prs_data.append(pr_dict)

            cont += 1
            print(cont)
            print(f"Usuario: {pr_dict['user']} Titulo: {pr_dict['title']}")

        print(f"Total de pull requests coletados: {len(prs_data)}")
        return prs_data


    def build_interactions(
        self,
        issues: list[dict[str, Any]],
        pull_requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        events = []

        for issue in issues:
            author = issue.get("user")
            number = issue.get("number")

            for comment in issue.get("comments", []):
                commenter = comment.get("user")
                if not commenter or not author:
                    continue

                events.append(
                    {
                        "type": "issue_comment",
                        "graphs": ["graph_1", "integrated"],
                        "source": commenter,
                        "target": author,
                        "issue_number": number,
                        "created_at": comment.get("created_at"),
                        "weight": 2
                    }
                )

                if commenter != author:
                    events.append(
                        {
                            "type": "issue_opened_commented",
                            "graphs": ["integrated"],
                            "source": commenter,
                            "target": author,
                            "issue_number": number,
                            "created_at": comment.get("created_at"),
                            "weight": 3
                        }
                    )

            closed_by = issue.get("closed_by")
            if closed_by and closed_by != author:
                events.append(
                    {
                        "type": "issue_closed",
                        "graphs": ["graph_2", "integrated"],
                        "source": closed_by,
                        "target": author,
                        "issue_number": number,
                        "closed_at": issue.get("closed_at"),
                        "weight": 3
                    }
                )

        for pr in pull_requests:
            author = pr.get("user")
            number = pr.get("number")

            for comment in pr.get("comments", []):
                commenter = comment.get("user")
                if not commenter or not author:
                    continue

                events.append(
                    {
                        "type": "pr_comment",
                        "graphs": ["graph_1", "integrated"],
                        "source": commenter,
                        "target": author,
                        "pull_number": number,
                        "created_at": comment.get("created_at"),
                        "weight": 2
                    }
                )

            for review in pr.get("reviews", []):
                reviewer = review.get("user")
                if not reviewer or not author:
                    continue

                events.append(
                    {
                        "type": "pr_review",
                        "graphs": ["graph_3", "integrated"],
                        "source": reviewer,
                        "target": author,
                        "pull_number": number,
                        "state": review.get("state"),
                        "submitted_at": review.get("submitted_at"),
                        "weight": 4
                    }
                )

            if pr.get("merged"):
                merged_by = pr.get("merged_by")
                if merged_by and merged_by != author:
                    events.append(
                        {
                            "type": "pr_merge",
                            "graphs": ["graph_3", "integrated"],
                            "source": merged_by,
                            "target": author,
                            "pull_number": number,
                            "merged_at": pr.get("merged_at"),
                            "weight": 5
                        }
                    )

        return {"events": events}
    