# AI Recruiter 🤖

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent recruitment system that leverages AI to match developers with job requirements by analyzing GitHub profiles and LinkedIn data.

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

### Endpoints

#### POST /recruit
Searches for developers matching the given requirements.

Request:
```json
    {
        "task_description": "Looking for senior Python developers with FastAPI experience",
        "limit": 50
    }
```

Response:
```json
    {
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