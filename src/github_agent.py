import os
import logging
from typing import Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI

from src.main import (
    get_repo_info,
    get_file_contents,
    analyze_code_complexity,
    generate_markdown_report
)

class GitHubRepositoryAgent:
    def __init__(self, github_token: str, openai_api_key: str):
        """_summary_
        Initialize the GitHub Repository Agent.
        Args:
            github_token (str): GitHub API token
            openai_api_key (str): OpenAI API key
        """
        # Initialize Language Model
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model='gpt-3.5-turbo',
            temperature=0.7
            )
        # Store GitHub token
        self.github_token = github_token
        
        # Define tools using existing functions
        self.tools = [
            Tool(
                name="Repository Analysis",
                func=self.analyze_repository,
                description="Comprhensive analysis of GitHub repo structure and code complexity"
            ),
            Tool(
                name="Code Complexity Insights",
                func=self.get_code_complexity,
                description="Retrieve detailed code complexity metrics for a specific file"
            ),
            Tool(
                name="Code Improvement Suggestions",
                func=self.generate_code_improvements,
                description="Generate AI-powered code improvement suggestions"
            )
        ]
        
        # Initialize Agent
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
    def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """ Analyze a GitHub repository

        Args:
            repo_url (str): URL of the GitHub repository

        Returns:
            Dict[str, Any]: Dictionary containing analysis results
        """
        # Fetch repository information
        repo_info = get_repo_info(repo_url)
        
        if not repo_info:
            return {"error": "Failed to fetch repository information"}
        
        # Analyze Files
        analysis_results = {}
        if 'contents' in repo_info:
            python_files = [f for f in repo_info['contents'] if f.endswith('.py')]
            
            for file in python_files[:3]: # Limit to top 3 files
                file_contents = get_file_contents(repo_url, file)
                if file_contents:
                    complexity = analyze_code_complexity(file_contents, file)
                    analysis_results[file] = complexity
                    
        return {
            'repository_info': repo_info,
            'analysis_results': analysis_results
        }
        
    def get_code_complexity(self, repo_url: str, file_path: str = None) -> Dict[str, Any]:
        """
        Get code complexity for a specific file
        
        :param repo_url: URL of the GitHub repository
        :param file_path: Path to the file (optional)
        :return: Code complexity metrics
        """
        # If no specific file is provided, try to find a main Python file
        if not file_path:
            # Fetch repository information to get contents
            repo_info = get_repo_info(repo_url)
            
            if not repo_info or 'contents' not in repo_info:
                return {"error": "Unable to retrieve repository contents"}
            
            # Find potential main Python files
            python_files = [
                f for f in repo_info['contents'] 
                if f.endswith('.py') and any(
                    keyword in f.lower() 
                    for keyword in ['main', 'core', 'app', '__init__', 'base']
                )
            ]
            
            # If no files found, take the first Python file
            if not python_files:
                python_files = [f for f in repo_info['contents'] if f.endswith('.py')]
            
            if not python_files:
                return {"error": "No Python files found in the repository"}
            
            # Select the first suitable file
            file_path = python_files[0]
        
        # Retrieve and analyze file contents
        file_contents = get_file_contents(repo_url, file_path)
        
        if not file_contents:
            return {"error": f"Unable to retrieve contents of {file_path}"}
        
        return analyze_code_complexity(file_contents, file_path)
        
    def generate_code_improvements(self, code_snippet: str) -> Dict[str, Any]:
        """ Generate AI-powered code improvement suggestions

        Args:
            code_snippet (str): Code to be improved

        Returns:
            Dict[str, Any]: Improvement suggestions
        """
        
        # Create a prompt template for code improvement suggestions
        improvement_template = PromptTemplate(
            input_variables=['code'],
            template="""
            Analyze the following code snippet and provide specific, actionable improvement suggestions:
            Code:
            ```python
            {code}
            ```
            Provide suggestions focusing on:
            1. Code readability
            2. Performance optimization
            3. Best practices
            4. Potential bugs or inefficiencies
            
            Suggestions:
            """
        )
        
        # Create a language model chain for code improvement suggestions
        improvement_chain = LLMChain(
            llm=self.llm,
            prompt=improvement_template
        )
        
        # Generate code improvement suggestions
        improvements = improvement_chain.run(code=code_snippet)
        
        return improvements
    
    def interact(self, query: str) -> str:
        """Main interaction method for the agent

        Args:
            query (str): User query

        Returns:
            str: Agent response
        """
        try:
            response = self.agent.run(query)
            return response
        except Exception as e:
            return f"An error occurred: {e}"
        
def main():
    """Interactive CLI for the GitHub Repository Agent
    """
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Intialize Agent
    agent = GitHubRepositoryAgent(
        github_token=os.getenv('GITHUB_TOKEN'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    # Interactive loop
    print("GitHub Repository AI Assistant")
    print("Enter 'exit' to quit")
    
    while True:
        query = input("\nEnter your query: ")
        if query.lower() == 'exit':
            break
        try:
            response= agent.interact(query)
            print("\nAgent Response:")
            print(response)
        except Exception as e:
            print(f"An error occurred: {e}")
if __name__ == "__main__":
    main()