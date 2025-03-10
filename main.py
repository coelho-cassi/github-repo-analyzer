import os # OS system interactions, file management
from dotenv import load_dotenv # Load environment variables from .env file
import requests # HTTP requests
import base64 # Base64 encoding
import re # Regular expressions
import pylint.lint # Pylint static analysis
from radon.complexity import cc_visit # Cyclomatic Complexity
from radon.metrics import h_visit # Halstead Metrics

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

def analyze_code_complexity(file_content, filename):
    try:
        # Cyclomattic Complexity
        """Measures the number of linearly independent paths through a program's source code
           Indicates how complex a piece of code is to test and maintain
           Counts decision points in code, the higher the number, the more complex the code"""
        complexity_results = cc_visit(file_content)
        
        # Halstead Metrics
        """Measures software complexity based on operators and operands
        Volume: Amount of information in code
        Difficulty: Potential for errors
        Effort: Estimated mental effort to understand code"""
        halstead_metrics = h_visit(file_content)
        
        # Pylint Static Analysis
        """Checks for programming errors, code style, and adherence to best practices"""
        pylint_output = analyze_with_pylint(file_content, filename)
        
        return{
            'cyclomatic_complexity': [
                {
                    'name': func.name,
                    'complexity': func.complexity,
                } for func in complexity_results
            ],
            'halstead_metrics': {
                'volume': halstead_metrics.volume,
                'difficulty': halstead_metrics.difficulty,
                'effort': halstead_metrics.effort,
            },
            'pylint_issues': pylint_output
        }
        
    except Exception as e:
        print(f"Error analyzing code complexity: {e}")
        return None

def analyze_with_pylint(file_content, filename):
     # Temporary file for pylint analysis
    with open(f'temp_{filename}', 'w') as temp_file:
        temp_file.write(file_content)
    
    try:
        # Capture Pylint output
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        # Run Pylint
        pylint.lint.Run([f'temp_{filename}'], exit=False)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        # Parse output
        output = redirected_output.getvalue()
        
        # Clean up temporary file
        os.remove(f'temp_{filename}')
        
        return output
    
    except Exception as e:
        print(f"Pylint analysis error: {e}")
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
    
    if repo_info and 'contents' in repo_info:
        print("\nCode Analysis:")
        for file in repo_info['contents']:
            # Analyze only Python files
            if file.endswith('.py'):
                print(f"\nAnalyzing {file}...")
                file_contents = get_file_contents(repo_url, file)
                
                if file_contents:
                    analysis_results = analyze_code_complexity(file_contents, file)
                    
                    if analysis_results:
                        print("Cyclomatic Complexity:")
                        for func in analysis_results['cyclomatic_complexity']:
                            print(f"  {func['name']}: {func['complexity']}")
                        
                        print("\nHalstead Metrics:")
                        print(f"  Volume: {analysis_results['halstead_metrics']['volume']}")
                        print(f"  Difficulty: {analysis_results['halstead_metrics']['difficulty']}")
                        print(f"  Effort: {analysis_results['halstead_metrics']['effort']}")
                        
                        print("\nPylint Issues:")
                        print(analysis_results['pylint_issues'] or "No issues found")
                        
if __name__ == "__main__":
    main()