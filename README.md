# AI Recruiter 🤖

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent recruitment system that leverages AI to match developers with job requirements by analyzing GitHub profiles and LinkedIn data.

## Important Notes

- This project is a work in progress and is not yet ready for production use.
- The project is not yet fully functional and is missing many features.
- The project is not yet fully tested and is missing many tests.
- This project is mostly implemented with AI.

## 🚀 Features

- Automated developer profile analysis
- Multi-platform data collection (GitHub, LinkedIn)
- AI-powered skill matching
- RESTful API interface
- Real-time developer search and filtering
- Rate-limited scraping to respect platform policies

## 📋 Prerequisites

- Python 3.9+
- MongoDB
- Docker (optional)
- Valid API keys for required services

## 🛠️ Installation

### Development Setup

1. Clone with development dependencies:
```bash
git clone <repository-url>
cd github-linkedin-analyzer
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Install LangGraph Studio:
```bash
pip install "langgraph[studio]"
```

4. Run with Studio support:
```bash
uvicorn main:app --reload --port 8000
```

### Development Tools

1. **Code Quality**:
   ```bash
   # Format code
   black .
   isort .
   
   # Type checking
   mypy .
   
   # Linting
   flake8
   ```

2. **Testing**:
   ```bash
   # Run tests
   pytest
   
   # Run tests with coverage
   pytest --cov=.
   ```

3. **API Documentation**:
   ```bash
   # Generate OpenAPI schema
   python -m scripts.generate_openapi
   ```

4. **LangGraph Studio**:
   - Visit `http://localhost:8000/docs` for Swagger UI
   - Visit `http://localhost:8000/studio/graph` for workflow visualization
   - Use trace IDs to inspect execution flow


### Using Docker

1. Clone the repository:
```bash
    git clone https://github.com/yourusername/ai-recruiter.git
    cd ai-recruiter
```

2. Build and run with Docker Compose:
```bash
    docker-compose up --build
```

### Manual Setup

1. Create and activate virtual environment:
```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
    pip install -r requirements.txt
```

3. Set up environment variables:
```bash
    cp .env.example .env
    # Edit .env with your configuration
```

4. Run the application:
```bash
    python main.py
```

## 🔧 Configuration

Create a `.env` file in the root directory:

```bash
    MONGODB_URI=your_mongodb_uri
    GITHUB_TOKEN=your_github_token
    ANTHROPIC_API_KEY=your_anthropic_key
    LINKEDIN_EMAIL=your_linkedin_email
    LINKEDIN_PASSWORD=your_linkedin_password
```

## 📚 API Documentation

### OpenAPI Documentation
The complete API documentation is available in OpenAPI/Swagger format:

1. **Interactive Documentation**:
   - Visit `/docs` for Swagger UI
   - Visit `/redoc` for ReDoc UI

2. **OpenAPI Specification**:
   - Available at `openapi.yml` in the root directory
   - Contains detailed schema definitions and endpoint specifications

3. **Main Endpoints**:
   - `POST /recruit`: Analyze GitHub contributors
   - `GET /studio/*`: LangGraph Studio integration endpoints

All endpoints support JSON request/response formats and include detailed error responses.

## 🔮 LangGraph Studio Integration

### Overview
The application includes LangGraph Studio integration for workflow visualization and debugging. The workflow consists of three main agents:

1. **Coordinator Agent**: Processes natural language input and coordinates other agents
2. **GitHub Agent**: Handles GitHub repository analysis
3. **LinkedIn Agent**: Manages LinkedIn profile extraction

### Studio Endpoints

#### GET /studio/config
Get LangGraph Studio configuration and metadata.

Response:
```json
{
    "title": "GitHub & LinkedIn Profile Analyzer",
    "description": "Analyze GitHub contributors and their LinkedIn profiles",
    "version": "1.0.0",
    "nodes": {
        "coordinator_node": {
            "description": "Processes user input and extracts repository information",
            "color": "#4CAF50"
        }
    }
}
```

#### GET /studio/graph
Get workflow graph visualization data showing the relationship between agents.

#### GET /studio/trace/{trace_id}
Get detailed execution trace with formatted messages and agent interactions.

#### GET /studio/tools
Get available tools and their descriptions for each agent.

#### GET /studio/traces
List recent execution traces with their status and duration.

### 🎯 Visualization
To view the workflow visualization:

1. Make a request to the `/recruit` endpoint
2. Copy the trace ID from the response
3. Visit `/studio/trace/{trace_id}` to view the execution flow
4. Use `/studio/graph` to view the overall workflow structure

### ⚙️ Configuration
The workflow visualization is configured through:

1. `langgraph.json` - Main configuration file
2. `agents/studio.py` - Studio-specific configurations
3. Environment variables in `.env`

### Endpoints

#### POST /recruit
Searches for developers matching the given requirements.

Request:
```json
    {
        "task_description": "bring me last 50 contributors of openai github repository",
        "limit": 50
    }
```

Response:
```json
{
    "repository": "openai/openai",
    "total_profiles": 50,
    "profiles_with_linkedin": 25,
    "profiles": [
        {
            "github_info": {
                "username": "string",
                "url": "string",
                "contributions": 0,
                "email": "string",
                "activity_metrics": {
                    "total_commits": 100,
                    "total_prs": 50,
                    "total_issues": 20,
                    "recent_commits": 30,
                    "recent_prs": 10,
                    "recent_issues": 5,
                    "languages": {
                        "Python": 50000,
                        "TypeScript": 30000
                    }
                }
            },
            "linkedin_info": {
                "url": "string",
                "current_position": "string",
                "company": "string",
                "location": "string",
                "industry": "string",
                "experience": [],
                "education": [],
                "skills": [],
                "certifications": []
            }
        }
    ]
}
        "developers": [
            {
                "id": "dev_123",
                "name": "John Doe",
                "github_profile": "https://github.com/johndoe",
                "linkedin_profile": "https://linkedin.com/in/johndoe",
                "skills": ["Python", "FastAPI", "MongoDB"],
                "experience_years": 8,
                "match_score": 0.95
            }
        ],
        "total": 1
    }
```

### API Documentation UI
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Development

## 🔍 Troubleshooting

### Common Issues

1. **GitHub API Rate Limiting**
   ```bash
   Error: GitHub API error: 403
   ```
   - Check your GitHub token permissions
   - Ensure you haven't exceeded API rate limits
   - Use authenticated requests

2. **LinkedIn Authentication**
   ```bash
   Error: Failed to login to LinkedIn
   ```
   - Verify LinkedIn credentials in .env
   - Check if LinkedIn has blocked automated access
   - Consider using a LinkedIn API token if available

3. **LangGraph Studio Issues**
   ```bash
   Error: Trace not found
   ```
   - Ensure workflow execution completed successfully
   - Check if trace ID is correct
   - Verify MongoDB connection

### Debug Mode

Enable debug mode for more detailed logs:
```bash
# In .env
DEBUG=true
LOG_LEVEL=debug

# Run with debug logging
uvicorn main:app --reload --log-level debug
```

### Getting Help

1. Check the [Issues](https://github.com/yourusername/github-linkedin-analyzer/issues) page
2. Review the documentation above
3. Contact support at support@example.com


### Running Tests

```bash
    # Install development dependencies
    pip install -r requirements-dev.txt
```

```bash
    # Run tests
    make test

    # Run linting
    make lint
```

### Project Structure

```
    .
    ├── agents/             # AI agent implementations
    ├── scrapers/          # Data collection modules
    │   ├── github_scraper.py
    │   └── linkedin_scraper.py
    ├── storage/           # Database models and operations
    ├── utils/            # Helper utilities
    │   └── rate_limiter.py
    └── main.py          # Application entry point
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

## 🐛 Troubleshooting

Common issues and solutions:

1. MongoDB Connection Issues
   - Verify MongoDB is running
   - Check connection string in .env
   - Ensure network connectivity

2. Scraping Issues
   - Verify API tokens are valid
   - Check rate limits
   - Ensure proper network access

3. Docker Issues
   - Run docker-compose down -v and rebuild
   - Check Docker logs
   - Verify port availability

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support:
- Open an issue in the GitHub repository
- Check existing issues for solutions