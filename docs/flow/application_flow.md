# Application Flow Documentation

## 1. High-Level Architecture

### 1.1 System Components
```mermaid
graph TD
    A[API Gateway] --> B[API Lambda]
    B --> C[GitHub Scraper Lambda]
    B --> D[LinkedIn Scraper Lambda]
    C --> E[DynamoDB State]
    D --> E
    E --> F[State Manager Lambda]
```

### 1.2 Event Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Gateway
    participant L as API Lambda
    participant G as GitHub Lambda
    participant N as LinkedIn Lambda
    participant D as DynamoDB
    
    C->>A: POST /recruit
    A->>L: Invoke
    L->>D: Create Initial State
    L-->>C: 202 Accepted
    L->>G: Invoke GitHub Scraper
    G->>D: Update State
    G->>N: Invoke LinkedIn Scraper
    N->>D: Update Final State
```

## 2. Detailed Workflow Steps

### 2.1 Request Processing
1. **API Request Handling**
   ```python
   async def process_request(event: Dict[str, Any]) -> Response:
       # Validate input
       # Create session
       # Initialize state
       # Trigger workflow
   ```

2. **State Initialization**
   ```python
   async def initialize_state(session_id: str) -> WorkflowState:
       # Create initial state
       # Set up workflow context
       # Save to DynamoDB
   ```

### 2.2 GitHub Processing
1. **Repository Analysis**
   ```mermaid
   graph LR
       A[Get Repository] --> B[List Contributors]
       B --> C[Process Each User]
       C --> D[Extract Metrics]
       D --> E[Update State]
   ```

2. **Contributor Processing**
   ```python
   async def process_contributor(
       username: str,
       repo: str
   ) -> GitHubProfile:
       # Get user details
       # Calculate metrics
       # Extract social links
       # Update state
   ```

### 2.3 LinkedIn Processing
1. **Profile Matching**
   ```mermaid
   graph TD
       A[Get LinkedIn URL] --> B{URL Valid?}
       B -->|Yes| C[Scrape Profile]
       B -->|No| D[Search by Name]
       C --> E[Process Profile]
       D --> E
       E --> F[Update State]
   ```

2. **Data Extraction**
   ```python
   async def extract_linkedin_data(
       profile_url: str
   ) -> LinkedInProfile:
       # Initialize scraper
       # Extract profile data
       # Process experience
       # Handle rate limits
   ```

## 3. State Management

### 3.1 State Transitions
```mermaid
stateDiagram-v2
    [*] --> Initialized
    Initialized --> GitHubProcessing
    GitHubProcessing --> LinkedInProcessing: Has LinkedIn URLs
    GitHubProcessing --> Completing: No LinkedIn URLs
    LinkedInProcessing --> Completing
    Completing --> [*]
```

### 3.2 State Updates
1. **Write Operations**
   ```python
   async def update_state(
       session_id: str,
       update_data: Dict[str, Any]
   ) -> None:
       # Validate update
       # Handle concurrency
       # Maintain history
   ```

2. **Read Operations**
   ```python
   async def get_latest_state(
       session_id: str
   ) -> WorkflowState:
       # Fetch latest
       # Handle missing data
       # Validate state
   ```

## 4. Error Handling

### 4.1 Error Flow
```mermaid
graph TD
    A[Error Occurs] --> B{Type?}
    B -->|Retryable| C[Retry Logic]
    B -->|Fatal| D[Error State]
    C -->|Max Retries| D
    C -->|Success| E[Continue Flow]
    D --> F[Notify Client]
```

### 4.2 Recovery Procedures
```python
async def handle_error(
    error: Exception,
    context: Dict[str, Any]
) -> None:
    # Log error
    # Update state
    # Trigger recovery
    # Notify monitoring
```

## 5. Data Flow

### 5.1 Profile Data Flow
```mermaid
graph LR
    A[Raw Data] --> B[Validation]
    B --> C[Enrichment]
    C --> D[Storage]
    D --> E[Response]
```

### 5.2 State Data Flow
```mermaid
graph TD
    A[State Change] --> B[Validation]
    B --> C[History]
    C --> D[Storage]
    D --> E[Notifications]
```

## 6. Monitoring and Metrics

### 6.1 Metric Collection
```python
class MetricPoints:
    REQUEST_START = "request.start"
    GITHUB_PROCESSING = "github.processing"
    LINKEDIN_PROCESSING = "linkedin.processing"
    STATE_UPDATE = "state.update"
    REQUEST_END = "request.end"
```

### 6.2 Tracing Flow
```mermaid
graph LR
    A[Request] -->|trace_id| B[GitHub]
    B -->|trace_id| C[LinkedIn]
    C -->|trace_id| D[Response]
```

## 7. Scaling Considerations

### 7.1 Concurrent Processing
```python
async def process_batch(
    profiles: List[str],
    batch_size: int = 10
) -> None:
    # Split into batches
    # Process concurrently
    # Handle failures
    # Merge results
```

### 7.2 Rate Limiting
```mermaid
graph TD
    A[Request] --> B{Rate Check}
    B -->|Under Limit| C[Process]
    B -->|Over Limit| D[Queue]
    D --> E[Delay]
    E --> B
```

## 8. Security Flow

### 8.1 Authentication Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant A as API Gateway
    participant L as Lambda
    participant S as Secrets

    C->>A: Request + API Key
    A->>L: Authenticated Request
    L->>S: Get Credentials
    S->>L: Return Credentials
```

### 8.2 Authorization Flow
```python
async def authorize_request(
    context: Dict[str, Any]
) -> bool:
    # Validate token
    # Check permissions
    # Rate limit check
    # Log access
```
