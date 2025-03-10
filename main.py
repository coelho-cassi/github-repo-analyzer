import os # OS system interactions, file management
from dotenv import load_dotenv # Load environment variables from .env file
import requests # HTTP requests
import base64 # Base64 encoding
import re # Regular expressions
import pylint.lint # Pylint static analysis
from radon.complexity import cc_visit # Cyclomatic Complexity
from radon.metrics import h_visit # Halstead Metrics
import markdown # Markdown rendering
from datetime import datetime # Date and time
import logging # Lo

# Load environment variables from .env file
load_dotenv()

# Github Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def setup_logging():
    # Create logs directory if it doesn't exist
     os.makedirs('logs', exist_ok=True)
     
     # Configure Logging
     logging.basicConfig(
         level=logging.INFO,
         format='%(asctime)s - %(levelname)s - %(message)s',
         handlers=[
             logging.FileHandler(f'logs/repo_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
             logging.StreamHandler()
         ]
     )
     
def error_handler(func):
    # Decorator to handle common exceptions and log errors
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.RequestException as e:
            logging.error(f"Network Error in {func.__name__}: {e}")
            return None
        except ValueError as e:
            logging.error(f"Value Error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    return wrapper

@error_handler
def get_repo_info(repo_url):
    # Extract username and repo name from the URL
    parts = repo_url.strip('/').split('/')
    username = parts[-2]
    repo_name = parts[-1]
    logging.info(f"Fetching repository information for {repo_url}")
    
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
 
@error_handler   
def get_file_contents (repo_url, file_path):
    parts = repo_url.strip('/').split('/')
    username = parts[-2]
    repo_name = parts[-1]
    logging.info(f"Retrieving contents of {file_path}")
    
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

@error_handler 
def analyze_code_complexity(file_content, filename):
    logging.info(f"Analyzing code complexity for {filename}")
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

def generate_markdown_report(repo_info, file_analyses):
    # Generate comprehensive markdown documentation for the repository
    report = f"# Repository Analysis Report: {repo_info['name']}\n\n"
    report += f"## Repository Overview\n"
    report += f"- **Description**: {repo_info.get('description', 'No description')}\n"
    report += f"- **Primary Language**: {repo_info.get('language', 'Unknown')}\n"
    report += f"- **Stars**: {repo_info.get('stars', 'N/A')}\n\n"
    report += f"- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report += "## Code Analysis Details\n"
    
    for filename, analysis in file_analyses.items():
        report += f"### File: {filename}\n"
        
        # Cyclomatic Complexity
        report += f"#### Cyclomatic Complexity\n"
        if analysis.get('cyclomatic_complexity'):
            for func in analysis['cyclomatic_complexity']:
                report += f"- **{func['name']}**: {func['complexity']} complexity\n"
        else:
                report += "- No complexity analysis available\n"
        
        # Halstead Metrics
        report += f"#### Halstead Metrics\n"
        if analysis.get('halstead_metrics'):
            metrics = analysis['halstead_metrics']
            report += f"- **Volume**: {metrics['volume']:.2f}\n"
            report += f"- **Difficulty**: {metrics['difficulty']:.2f}\n"
            report += f"- **Effort**: {metrics['effort']:.2f}\n"
        else:
                report += "- No Halstead metrics available\n"   
                
        # Pylint Issues
        report += "#### Code Quality Issues\n"
        if analysis.get('pylint_issues'):
            report += "```\n"
            report += analysis['pylint_issues']
            report += "\n```\n"
        else:
            report += "- No significant issues detected\n"
         
        report += "\n---\n"
        
        # Save markdown report to a file
        output_dir = 'repository_analysis'
        os.markdir(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{repo_info['name']}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        with open(output_file, 'w') as f:
            f.write(report)
            
        # Convert to HTML
        html_output = os.path.join(output_dir, f"{repo_info['name']}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        html_content = markdown.markdown(report)
        
        with open(html_output, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Repository Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    code {{ background-color: #f4f4f4; padding: 2px 4px; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """)
            
            return output_file, html_output

def validate_github_url(url):
    # Validate the GitHub repository URL
    github_pattern = r'^https?://github\.com/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+/?$'
    if not re.match(github_pattern, url):
        logging.error(f"Invalid GitHub URL: {url}")
        raise ValueError("Invalid GitHub repository URL")
    return url
                  
def main():
    
    repo_url = input("Enter the GitHub repository URL: ")
    repo_info = get_repo_info(repo_url)
    
    # Set up logging
    setup_logging()
    
    try:
        # URL input with validation
        while True:
            repo_url = input("Enter the GitHub repository URL: ")
            try:
                validated_url = validate_github_url(repo_url)
                break
            except ValueError as e:
                logging.error(str(e))
                print(str(e))
                print("Please enter a valid GitHub repository URL.")

    
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
        # Code analysis
        if 'contents' in repo_info:
            file_analyses = {}
            
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
                            
                            file_analyses[file] = analysis_results
        
        # Generate documentation
        if file_analyses:
            md_report, html_report = generate_markdown_report(repo_info, file_analyses)
            print(f"\nAnalysis complete!")
            print(f"Markdown Report: {md_report}")
            print(f"HTML Report: {html_report}")
    except KeyboardInterrupt:
        logging.info("Analysis interrupted by user.")
        print("\nOperation cancelled.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in main execution: {e}")
        print(f"An error occurred: {e}")
                
if __name__ == "__main__":
    main()