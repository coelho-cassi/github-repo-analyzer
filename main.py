import os
from dotenv import load_dotenv
import requests
import base64

# Load environment variables from .env file
load_dotenv()

# Github Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_repo_info(repo_url):
    # Extract username and repo name from the URL
    parts = repo_url.strip('/').split('/')
    username = parts[-2]
    repo_name = parts[-1]
    
    # GitHub API endpoint
    base_url = f'https://api.github.com/repos/{username}/{repo_name}'
    
    # Initial Github API interaction
    headers = {
        'Authorization' : f'token {GITHUB_TOKEN}',
        'Accept' : 'application/vnd.github.v3+json'
    }
    
    try:
        # Fetch repository metadata
        repo_response = requests.get(base_url, headers=headers)
        repo_response.raise_for_status()  # Raise error for bad responses
        repo_data = repo_response.json()

        # Fetch repository contents
        contents_url = f'{base_url}/contents'
        contents_response = requests.get(contents_url, headers=headers)
        contents_response.raise_for_status()
        contents_data = contents_response.json()

        return {
            'name': repo_data['name'],
            'description': repo_data['description'],
            'language': repo_data['language'],
            'stars': repo_data['stargazers_count'],
            'contents': [item['name'] for item in contents_data]
        }

    except requests.RequestException as e:
        print(f"Error fetching repository information: {e}")
        return None
    
def get_file_contents (repo_url, file_path):
    parts = repo_url.strip('/').split('/')
    username = parts[-2]
    repo_name = parts[-1]
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    url = f'https://api.github.com/repos/{username}/{repo_name}/contents/{file_path}'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        file_data = response.json()
        
        # Decode the file content
        file_content = base64.b64decode(file_data['content']).decode('utf-8')
        return file_content
    
    except requests.RequestException as e:
        print(f"Error fetching file contents: {e}")
        return None

def main():
    repo_url = input("Enter the GitHub repository URL: ")
    repo_info = get_repo_info(repo_url)
    
    if repo_info:
        print("Repository Information:")
        for key, value in repo_info.items():
            print(f"{key.capitalize()}: {value}")
            
        if 'contents' in repo_info:
            print("\nAvailable Files:")
            for file in repo_info['contents']:
                print(file)
                
                file_to_read = input("\nEnter the file name to read (or press Enter to skip): ")
                if file_to_read:
                    file_contents = get_file_contents(repo_url, file_to_read)
                    if file_contents:
                        print(f"\nContents of {file_to_read}:")
                        print(file_contents[:500] + "..." if len(file_contents) > 500 else file_contents)
    
if __name__ == "__main__":
    main()