# GitHub LinkedIn Profile Analyzer Documentation

## Project Documentation Structure

```
docs/
├── requirements/
│   └── project_requirements.md     # Detailed project requirements and specifications
├── tech_stack/
│   └── tech_stack.md              # Technology stack and package documentation
├── schema/
│   └── schema_design.md           # Data models and schema design
├── flow/
│   └── application_flow.md        # Application workflow and process flows
└── index.md                       # This documentation index
```

## 1. Quick Start

### 1.1 Development Setup
```bash
# Clone repository
git clone <repository-url>
cd github-linkedin-analyzer

# Set up environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 1.2 Run Application
```bash
# Local development
uvicorn main:app --reload

# AWS deployment
python scripts/deploy.py --environment dev --s3-bucket your-bucket
```

## 2. Documentation Sections

### 2.1 [Project Requirements](requirements/project_requirements.md)
- Project overview and objectives
- Functional requirements
- Non-functional requirements
- Technical requirements
- Success criteria
- Future considerations

### 2.2 [Technical Stack](tech_stack/tech_stack.md)
- Core technology stack
- Package dependencies
- Version management
- Security considerations
- Performance optimization
- Maintenance procedures

### 2.3 [Schema Design](schema/schema_design.md)
- Data models
- State management
- Cache management
- API schemas
- Schema evolution
- Data retention
- Validation rules

### 2.4 [Application Flow](flow/application_flow.md)
- High-level architecture
- Detailed workflow steps
- State management
- Error handling
- Data flow
- Monitoring and metrics
- Scaling considerations
- Security flow

## 3. Key Concepts

### 3.1 State Management
- Asynchronous workflow processing
- DynamoDB state persistence
- Concurrent state updates
- State validation and recovery

### 3.2 Data Processing
- GitHub API integration
- LinkedIn profile scraping
- Data enrichment
- Profile matching
- Metrics calculation

### 3.3 AWS Integration
- Serverless architecture
- Lambda functions
- DynamoDB tables
- API Gateway
- Monitoring and logging

### 3.4 Security
- API authentication
- Credential management
- Rate limiting
- Data protection

## 4. Common Tasks

### 4.1 Development Tasks
```bash
# Run tests
pytest

# Type checking
mypy .

# Code formatting
black .
isort .

# Lint code
flake8
```

### 4.2 Deployment Tasks
```bash
# Build Lambda layers
./scripts/build_layers.sh

# Deploy to AWS
./scripts/deploy.py --environment prod

# Update configuration
aws ssm put-parameter --name /prod/github-token --value "token" --type SecureString
```

### 4.3 Monitoring Tasks
```bash
# View logs
aws logs tail /aws/lambda/github-linkedin-analyzer-prod

# Check metrics
aws cloudwatch get-metric-statistics --namespace GitHubLinkedInAnalyzer

# Trace requests
aws xray get-trace-summaries
```

## 5. Troubleshooting

### 5.1 Common Issues
- API rate limiting
- State consistency
- Lambda timeouts
- Scraping failures

### 5.2 Debug Tools
- AWS X-Ray traces
- CloudWatch logs
- DynamoDB streams
- State inspection

### 5.3 Support Resources
- GitHub repository
- AWS documentation
- Package documentation
- Support channels

## 6. Contributing

### 6.1 Development Flow
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

### 6.2 Code Standards
- Type hints required
- Test coverage > 80%
- Documentation updates
- Code review process

### 6.3 Release Process
1. Version bump
2. Changelog update
3. Documentation review
4. Deployment steps
5. Monitoring period

## 7. API Reference

### 7.1 Endpoints
- POST /recruit
- GET /status/{session_id}
- GET /metrics

### 7.2 Request/Response Examples
```json
// Request
{
    "task_description": "find contributors of openai/gpt-3",
    "limit": 50
}

// Response
{
    "session_id": "uuid",
    "status": "processing",
    "message": "Request accepted"
}
```

### 7.3 Error Handling
- HTTP status codes
- Error response format
- Retry mechanisms
- Rate limit handling
