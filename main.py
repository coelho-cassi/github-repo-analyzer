import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# Github Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_repo_info(repo_url):
    #Initial Github API interaction
    headers = {
        'Authorization' : f'token {GITHUB_TOKEN}'
    }
    #API call logic will go here
    pass

def main():
    repo_url = input("Enter the GitHub repository URL: ")
    repo_info = get_repo_info(repo_url)
    
if __name__ == "__main__":
    main()