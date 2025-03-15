# GitHub Repository AI Analyzer

## Project Overview

GitHub Repository AI Analyzer is an advanced tool that leverages AI and code analysis techniques to provide deep insights into GitHub repositories. The project combines static code analysis, complexity metrics, and AI-powered insights to help developers understand code structure and quality.

## Features

### Code Analysis Capabilities
- Repository information retrieval
- Code complexity metrics
- Cyclomatic complexity analysis
- Halstead metrics calculation
- Pylint static code analysis
- AI-powered code improvement suggestions

### AI Agent Functionality
- Interactive repository exploration
- Intelligent code insights
- Multi-repository analysis support
- Dynamic file selection

## Technologies Used

- Python
- GitHub API
- OpenAI GPT
- LangChain
- Radon (Code Complexity)
- Pylint (Static Analysis)

## Prerequisites

- Python 3.10+
- GitHub Personal Access Token
- OpenAI API Key

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/github-repo-analyzer.git
cd github-repo-analyzer
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate # On Windows use 'venv\Scripts\activate'
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
Create a `.env` file in the project root:
```bash
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
```

## Usage
Run the AI agent
```bash
python -m src.github_agent
```

### Example Queries
- "Analyze the Flask repository"
- "What are the most complex files in the Django project?"
- "Generate code improvement suggestions"

## Project Structure
```
github-repo-analyzer/
│
├── src/
│   ├── main.py           # Core repository analysis
│   └── github_agent.py   # AI-powered agent
├── config/
│   └── config.yaml       # Configuration settings
├── logs/                 # Logging directory
└── repository_analysis/  # Generated reports
