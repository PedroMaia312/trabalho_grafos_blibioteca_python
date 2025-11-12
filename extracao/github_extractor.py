from github import Github, Repository

class GithubExtractor:
    
    def __init__(self, github_token: str, repo_name: str):
        try:
            self.conection = Github(github_token)
            self.repo: Repository = self.conection.get_repo(repo_name)
            
            print(f"Conexão estabelecida com sucesso ao repositório: {self.repo.full_name}")
            
        except Exception as e:
            raise Exception(f"Erro ao conectar ao GitHub ou carregar o repositório: {e}")