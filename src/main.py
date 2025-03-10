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
import yaml # YAML parsing
from typing import Dict, Any # Type hints

# Load environment variables from .env file
load_dotenv()

# Github Token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def setup_logging(logging_config: Dict[str, Any] = None):
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Default logging configuration
    log_level = logging.INFO
    log_file = os.path.join('logs', f'repo_analyzer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Override with provided configuration if available
    if logging_config:
        log_level = getattr(logging, logging_config.get('level', 'INFO').upper())
        log_file = os.path.join(
            logging_config.get('file_path', 'logs'), 
            f'repo_analyzer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
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
        # Cyclomatic Complexity
        """Measures the number of linearly independent paths through a program's source code
           Indicates how complex a piece of code is to test and maintain
           Counts decision points in code, the higher the number, the more complex the code"""
        complexity_results = cc_visit(file_content)
        
        # Halstead Metrics
        """Measures software complexity based on operators and operands
        Volume: Amount of information in code
        Difficulty: Potential for errors
        Effort: Estimated mental effort to understand code"""
        try:
            halstead_metrics = h_visit(file_content)
            
            if isinstance(halstead_metrics, list):
                if halstead_metrics:
                    halstead_data = {
                        'volume': halstead_metrics.volume,
                        'difficulty': halstead_metrics.difficulty,
                        'effort': halstead_metrics.effort,
                    }
                else: 
                    halstead_data = {
                        'volume': 0,
                        'difficulty': 0,
                        'effort': 0
                    }
            else:
                halstead_data = {
                    'volume': getattr(halstead_metrics, 'volume', 0),
                    'difficulty': getattr(halstead_metrics, 'difficulty', 0),
                    'effort': getattr(halstead_metrics, 'effort', 0)
                }
        except Exception as e:
            logging.error(f"Error calculating Halstead metrics: {e}")
            halstead_data = {
                'volume': 0,
                'difficulty': 0,
                'effort': 0
            }
        
        # Pylint Static Analysis
        """Checks for programming errors, code style, and adherence to best practices"""
        try:
            pylint_output = analyze_with_pylint(file_content, filename)
        except Exception as e:
            logging.error(f"Pylint analysis error: {e}")
            pylint_output = f"Unable to perform Pylint analysis"
        
        return{
            'cyclomatic_complexity': [
                {
                    'name': func.name,
                    'complexity': func.complexity,
                } for func in complexity_results
            ],
            'halstead_metrics': halstead_data,
            'pylint_issues': pylint_output
        }
        
    except Exception as e:
        print(f"Error analyzing code complexity: {e}")
        return None

def analyze_with_pylint(file_content, filename):
     # Temporary file for pylint analysis
    try:
        # Temporary file for pylint analysis
        with open(f'temp_{filename}', 'w', encoding='utf-8') as temp_file:
            temp_file.write(file_content)
        
        # Capture Pylint output
        from io import StringIO
        import sys
        
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        # Run Pylint
        from pylint import lint
        lint.Run([f'temp_{filename}'], exit=False)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        # Get output
        output = redirected_output.getvalue()
        
        # Clean up temporary file
        os.remove(f'temp_{filename}')
        
        return output
    except Exception as e:
        logging.error(f"Pylint analysis error: {e}")
        return f"Unable to perform Pylint analysis: {e}"

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
        os.makedirs(output_dir, exist_ok=True)
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

def load_configuration(config_path: str = None) -> Dict[str, Any]:
    # Determine the correct path to config.yaml
    if config_path is None:
        # Get the absolute path to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        
        validate_config(config)
        return config
    except FileNotFoundError:
        logging.warning(f"Configuration file not found at {config_path}. Using default settings.")
        return get_default_config()
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration: {e}")
        return get_default_config()

def validate_config(config: Dict[str, Any]):
    # Validate configuration structure and values
    
    required_keys = ['github', 'logging', 'report']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

def get_default_config() -> Dict[str, Any]:
    # Provide default configuration if loading fails
    return {
        'github': {
            'api_version': 'v3',
            'max_file_size': 1048576
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/'
        },
        'report': {
            'output_formats': ['markdown', 'html'],
            'include_sections': ['complexity', 'halstead_metrics', 'pylint_issues']
        }
    }
                  
def main():
    # Load configuration
    try:
        config = load_configuration()
        
        # Setup logging based on configuration
        setup_logging(config['logging'])
        
        # URL Input with Validation
        while True:
            repo_url = input("Enter GitHub Repository URL: ")
            try:
                validated_url = validate_github_url(repo_url)
                break
            except ValueError as e:
                print(str(e))
                print("Please enter a valid GitHub repository URL.")
        
        # Fetch repository information
        repo_info = get_repo_info(validated_url)
        
        if repo_info:
            # Print basic repository information
            print("Repository Information:")
            for key, value in repo_info.items():
                print(f"{key.capitalize()}: {value}")
            
            # Optional: Interactive file reading
            if 'contents' in repo_info:
                print("\nAvailable Files:")
                for file in repo_info['contents']:
                    print(file)
                
                file_to_read = input("\nEnter a file to read (or press Enter to skip): ")
                if file_to_read:
                    file_contents = get_file_contents(validated_url, file_to_read)
                    if file_contents:
                        print(f"\nContents of {file_to_read}:")
                        print(file_contents[:500] + "..." if len(file_contents) > 500 else file_contents)
            
            # Code Analysis
            if 'contents' in repo_info:
                file_analyses = {}
                
                print("\nCode Analysis:")
                for file in repo_info['contents']:
                    # Analyze only Python files
                    # Use configuration to determine analysis options
                    if (file.endswith('.py') and 
                        config['report'].get('include_sections', []) and 
                        len(file_contents) <= config['github'].get('max_file_size', 1048576)):
                        
                        print(f"\nAnalyzing {file}...")
                        file_contents = get_file_contents(validated_url, file)
                        
                        if file_contents:
                            analysis_results = analyze_code_complexity(file_contents, file)
                            
                            if analysis_results:
                                # Optional: Print detailed analysis to console
                                print("Cyclomatic Complexity:")
                                for func in analysis_results['cyclomatic_complexity']:
                                    print(f"  {func['name']}: {func['complexity']}")
                                
                                print("\nHalstead Metrics:")
                                print(f"  Volume: {analysis_results['halstead_metrics']['volume']}")
                                print(f"  Difficulty: {analysis_results['halstead_metrics']['difficulty']}")
                                print(f"  Effort: {analysis_results['halstead_metrics']['effort']}")
                                
                                print("\nPylint Issues:")
                                print(analysis_results['pylint_issues'] or "No issues found")
                                
                                # Store analysis for report generation
                                file_analyses[file] = analysis_results
                
                # Generate documentation based on configuration
                if file_analyses:
                    output_formats = config['report'].get('output_formats', ['markdown', 'html'])
                    
                    md_report, html_report = generate_markdown_report(repo_info, file_analyses)
                    
                    print(f"\nAnalysis complete!")
                    print(f"Markdown Report: {md_report}")
                    print(f"HTML Report: {html_report}")
    
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user")
        print("\nOperation cancelled.")
    except Exception as e:
        logging.critical(f"Unexpected error in main execution: {e}")
        print(f"An unexpected error occurred: {e}")
                
if __name__ == "__main__":
    main()