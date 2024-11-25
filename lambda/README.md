# GitHub LinkedIn Analyzer - Serverless Implementation

## Architecture

### AWS Services Used
- AWS Lambda for serverless compute
- Amazon DynamoDB for state management and caching
- Amazon API Gateway for REST API
- AWS Secrets Manager for credentials
- AWS X-Ray for tracing
- Amazon CloudWatch for monitoring and logging

### Components
1. **API Handler** (`lambda/api/handler.py`)
   - Handles incoming API requests
   - Initiates workflow
   - Manages session state

2. **GitHub Scraper** (`lambda/github_scraper/handler.py`)
   - Fetches repository contributors
   - Extracts user information
   - Processes activity metrics

3. **State Management** (`infrastructure/state/manager.py`)
   - Manages workflow state in DynamoDB
   - Handles concurrent updates
   - Provides type-safe interface

4. **Common Layer** (`layers/common/`)
   - Shared utilities and dependencies
   - Type definitions
   - Error handling

## Deployment

### Prerequisites
1. AWS CLI configured with appropriate credentials
2. SAM CLI installed
3. Python 3.9+
4. Required secrets in AWS Secrets Manager:
   ```
   /${Environment}/github-linkedin-analyzer/github-token
   /${Environment}/github-linkedin-analyzer/anthropic-key
   /${Environment}/github-linkedin-analyzer/linkedin-email
   /${Environment}/github-linkedin-analyzer/linkedin-password
   ```

### Deployment Steps
1. Build and deploy using SAM:
   ```bash
   # Install dependencies
   pip install -r lambda/requirements.txt

   # Deploy with SAM
   sam build
   sam deploy --guided
   ```

2. Update environment variables:
   ```bash
   aws ssm put-parameter \
       --name /dev/github-linkedin-analyzer/github-token \
       --value "your-github-token" \
       --type SecureString
   ```

### Testing
Run the test suite:
```bash
# Install test dependencies
pip install -r lambda/requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest lambda/tests/
```

## State Management

### DynamoDB Schema

#### State Table
- Partition Key: `session_id` (String)
- Sort Key: `timestamp` (String)
- TTL: `ttl` (Number)

#### Cache Table
- Partition Key: `profile_id` (String)
- TTL: `ttl` (Number)

### State Flow
1. Initial state created by API handler
2. Updated by GitHub scraper
3. Final state includes all collected data

## Monitoring

### CloudWatch Metrics
- Request counts
- Error rates
- Duration metrics
- State transitions

### X-Ray Tracing
- End-to-end request tracing
- Performance analysis
- Error tracking

### Logs
- Structured JSON logging
- Log correlation with X-Ray
- Error tracking with context

## Error Handling

### Retry Mechanism
- Configurable retry attempts
- Exponential backoff
- DynamoDB conditional writes

### Rate Limiting
- GitHub API rate limit handling
- LinkedIn scraping limits
- Concurrent execution limits

## Security

### IAM Roles
- Least privilege principle
- Separate roles per function
- Resource-based policies

### Secrets
- AWS Secrets Manager integration
- Encryption at rest
- Secure environment variables

### API Security
- API Gateway authentication
- CORS configuration
- Request validation

## Local Development

### Setup Local Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r lambda/requirements.txt
pip install -r requirements-dev.txt

# Set up local DynamoDB
docker-compose up -d dynamodb-local
```

### Local Testing
```bash
# Run local API
sam local start-api

# Test specific function
sam local invoke "APIFunction" -e events/api_event.json
```

### Development Tools
- AWS SAM CLI for local testing
- DynamoDB local for development
- pytest for testing
- mypy for type checking

## Troubleshooting

### Common Issues
1. **DynamoDB Errors**
   - Check table existence
   - Verify IAM permissions
   - Validate key schema

2. **Lambda Timeouts**
   - Check function timeout settings
   - Monitor memory usage
   - Optimize code performance

3. **API Gateway Issues**
   - Verify CORS settings
   - Check request/response mapping
   - Monitor integration timeouts

### Debugging
- Enable X-Ray tracing
- Use structured logging
- Monitor CloudWatch metrics

## Production Considerations

### Scaling
- Configure concurrency limits
- Monitor DynamoDB capacity
- Set appropriate timeouts

### Costs
- Monitor Lambda execution
- DynamoDB usage optimization
- API Gateway request volume

### Maintenance
- Regular dependency updates
- Security patch management
- Performance optimization
