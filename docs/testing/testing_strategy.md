# Testing Strategy Documentation

## 1. Testing Architecture

### 1.1 Test Organization
```
tests/
├── unit/                      # Unit tests
│   ├── agents/               # Agent tests
│   ├── scrapers/            # Scraper tests
│   └── utils/               # Utility tests
│
├── integration/              # Integration tests
│   ├── api/                 # API tests
│   ├── workflow/            # Workflow tests
│   └── storage/            # Storage tests
│
├── e2e/                     # End-to-end tests
│   └── scenarios/          # Test scenarios
│
└── fixtures/                # Test fixtures
    ├── github/             # GitHub API fixtures
    ├── linkedin/           # LinkedIn data fixtures
    └── states/             # State fixtures
```

### 1.2 Test Dependencies
```python
# test-requirements.txt
pytest>=7.4.0
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-mock>=3.11.1
pytest-timeout>=2.1.0
pytest-xdist>=3.3.1
aioresponses>=0.7.4
moto>=4.2.0
fakeredis>=2.10.0
responses>=0.23.1
```

## 2. Unit Testing

### 2.1 Agent Tests
```python
@pytest.mark.asyncio
async def test_github_agent_processing():
    """Test GitHub agent processing logic."""
    agent = GitHubAgent()
    input_data = {
        "repository": "test/repo",
        "limit": 5
    }
    
    result = await agent.process(input_data)
    assert result["profiles"]
    assert len(result["profiles"]) <= 5

@pytest.mark.asyncio
async def test_linkedin_agent_processing():
    """Test LinkedIn agent processing."""
    agent = LinkedInAgent()
    input_urls = ["https://linkedin.com/in/test"]
    
    result = await agent.process({"profile_urls": input_urls})
    assert result["profiles"]
```

### 2.2 State Management Tests
```python
class TestStateManager:
    @pytest.fixture
    async def state_manager(self):
        return StateManager(table_name="test-table")

    @pytest.mark.asyncio
    async def test_state_persistence(self, state_manager):
        """Test state save and retrieval."""
        state = {
            "session_id": "test-123",
            "messages": [{"content": "test", "type": "system"}]
        }
        
        await state_manager.save_state("test-123", state)
        retrieved = await state_manager.get_latest_state("test-123")
        
        assert retrieved["messages"] == state["messages"]
```

## 3. Integration Testing

### 3.1 API Integration Tests
```python
@pytest.mark.asyncio
async def test_recruit_endpoint():
    """Test complete recruitment flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/recruit",
            json={
                "task_description": "find contributors",
                "limit": 5
            }
        )
        
        assert response.status_code == 202
        assert "session_id" in response.json()
```

### 3.2 Workflow Integration Tests
```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test end-to-end workflow execution."""
    workflow = create_workflow()
    initial_state = {
        "messages": [{"content": "test task", "type": "human"}],
        "github_data": {},
        "linkedin_data": {}
    }
    
    result = await workflow.ainvoke(initial_state)
    assert result["final_response"]
```

## 4. End-to-End Testing

### 4.1 Scenario Tests
```python
@pytest.mark.e2e
async def test_github_to_linkedin_flow():
    """Test complete GitHub to LinkedIn flow."""
    async with TestClient() as client:
        # Initialize request
        init_response = await client.post("/recruit", json={
            "task_description": "find top contributors"
        })
        session_id = init_response.json()["session_id"]
        
        # Poll for completion
        while True:
            status = await client.get(f"/status/{session_id}")
            if status.json()["status"] == "completed":
                break
            await asyncio.sleep(1)
        
        # Verify results
        results = await client.get(f"/results/{session_id}")
        assert results.json()["profiles"]
```

### 4.2 Load Testing
```python
@pytest.mark.load
async def test_concurrent_requests():
    """Test system under load."""
    async def make_request():
        async with AsyncClient() as client:
            return await client.post("/recruit", json={
                "task_description": "test request"
            })
    
    # Execute 10 concurrent requests
    requests = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*requests)
    
    assert all(r.status_code == 202 for r in responses)
```

## 5. Mock and Fixture Management

### 5.1 API Mocks
```python
@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    with aioresponses() as m:
        m.get(
            "https://api.github.com/repos/test/repo/contributors",
            payload=[{"login": "test_user"}]
        )
        yield m

@pytest.fixture
def mock_linkedin_scraper():
    """Mock LinkedIn scraper."""
    async def mock_scrape(*args, **kwargs):
        return {
            "name": "Test User",
            "position": "Developer"
        }
    return mock_scrape
```

### 5.2 State Fixtures
```python
@pytest.fixture
def workflow_state():
    """Provide test workflow state."""
    return {
        "session_id": "test-123",
        "messages": [],
        "github_data": {
            "repository": "test/repo",
            "contributors": []
        },
        "linkedin_data": {
            "profiles": []
        }
    }
```

## 6. Coverage and Quality

### 6.1 Coverage Configuration
```ini
# pytest.ini
[pytest]
addopts = --cov=app --cov-report=term-missing --cov-fail-under=80
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    load: Load tests
```

### 6.2 Quality Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
```

## 7. CI/CD Integration

### 7.1 Test Workflow
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt -r test-requirements.txt
      - name: Run tests
        run: pytest
```

### 7.2 Test Reports
```python
def pytest_terminal_summary(terminalreporter):
    """Generate test summary report."""
    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    
    print(f"\nTest Summary:")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
```
