import os
from dotenv import load_dotenv
from github_extractor import GithubExtractor

if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.environ.get("TOKEN_GITHUB")
    repo = "boto/boto3"

    extractor = GithubExtractor(TOKEN, repo)
    