# Metrics Reference Guide

## Overview
This document details all available metrics for the GitHub LinkedIn Analyzer system, including their definitions, units, dimensions, and recommended usage.

## Core Service Metrics

### API Layer
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| APIRequests | Total API requests | Count | Service, Endpoint | Traffic monitoring |
| APIErrors | Failed API requests | Count | Service, ErrorType | Error tracking |
| RequestDuration | API request latency | Milliseconds | Service, Endpoint | Performance monitoring |
| ConcurrentExecutions | Concurrent Lambda executions | Count | Service | Capacity planning |

### GitHub Integration
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| ContributorsFetched | Number of contributors retrieved | Count | Repository | Data volume tracking |
| GitHubScrapingErrors | GitHub scraping failures | Count | ErrorType | Error monitoring |
| GitHubRateLimit | Remaining API rate limit | Count | - | Capacity management |
| ContributorsProcessed | Successfully processed contributors | Count | Status | Success tracking |

### LinkedIn Integration
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| LinkedInProfilesProcessed | Processed LinkedIn profiles | Count | Status | Processing tracking |
| LinkedInScrapingErrors | LinkedIn scraping failures | Count | ErrorType | Error monitoring |
| ProfileMatchRate | Successful profile matches | Percent | - | Match quality tracking |
| ScrapingDuration | Profile scraping duration | Milliseconds | - | Performance monitoring |

### State Management
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| StateUpdates | State update operations | Count | Operation | State tracking |
| StateProcessingLag | State processing delay | Seconds | - | Performance monitoring |
| StateSizeBytes | Size of state data | Bytes | - | Resource monitoring |
| StateErrors | State operation errors | Count | ErrorType | Error tracking |

## Performance Metrics

### Lambda Performance
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| MemoryUtilization | Lambda memory usage | Percent | Function | Resource monitoring |
| ColdStarts | Lambda cold starts | Count | Function | Performance tracking |
| Duration | Function execution time | Milliseconds | Function | Performance monitoring |
| Timeouts | Function timeouts | Count | Function | Error tracking |

### Cache Performance
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| CacheHits | Successful cache hits | Count | CacheType | Cache effectiveness |
| CacheMisses | Cache misses | Count | CacheType | Cache optimization |
| CacheLatency | Cache operation latency | Milliseconds | Operation | Performance monitoring |
| CacheSize | Size of cached data | Bytes | CacheType | Resource monitoring |

### DynamoDB Metrics
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| ThrottledRequests | Throttled DynamoDB requests | Count | TableName | Capacity monitoring |
| ConsumedCapacity | DynamoDB capacity units used | Count | TableName, Operation | Resource planning |
| ItemSize | Size of DynamoDB items | Bytes | TableName | Storage monitoring |
| QueryLatency | DynamoDB query latency | Milliseconds | TableName | Performance tracking |

## Operational Metrics

### System Health
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| HealthCheckStatus | System health check status | Count | Component | Health monitoring |
| ErrorRate | Overall system error rate | Percent | Service | Error tracking |
| ServiceAvailability | Service uptime | Percent | Service | Availability tracking |
| RecoveryTime | Error recovery duration | Seconds | ErrorType | Resilience monitoring |

### Business Metrics
| Metric Name | Description | Unit | Dimensions | Recommended Use |
|------------|-------------|------|------------|-----------------|
| ProcessedProfiles | Total profiles processed | Count | Type | Business tracking |
| SuccessfulMatches | Successful profile matches | Count | - | Success tracking |
| ProcessingCost | Estimated processing cost | USD | Service | Cost monitoring |
| DataQualityScore | Profile data quality score | Percent | DataType | Quality monitoring |

## Using Metrics

### Best Practices
1. **Aggregation**: Use appropriate statistics (Sum, Average, p90, etc.) based on metric type
2. **Dimensions**: Include relevant dimensions for detailed analysis
3. **Time Periods**: Consider appropriate time windows for different metrics
4. **Thresholds**: Set meaningful thresholds based on business requirements

### Example Queries

#### Monitor API Performance
```python
metrics.add_metric(
    name="RequestDuration",
    value=duration,
    unit=MetricUnit.Milliseconds,
    dimensions={"Service": "api", "Endpoint": "/recruit"}
)
```

#### Track Processing Success
```python
metrics.add_metric(
    name="ProcessedProfiles",
    value=len(processed_profiles),
    unit=MetricUnit.Count,
    dimensions={"Type": "github"}
)
```

### Alerting Recommendations

1. **Critical Alerts**
   - High error rates (> 5%)
   - Service unavailability
   - Rate limit approaching
   - DynamoDB throttling

2. **Warning Alerts**
   - Increased latency
   - Low cache hit rates
   - High memory utilization
   - Increased cold starts

3. **Information Alerts**
   - Large batch processing completion
   - Daily processing statistics
   - Cost threshold notifications

### Dashboard Organization

1. **Operations Dashboard**
   - Service health
   - Error rates
   - API performance
   - Resource utilization

2. **Business Dashboard**
   - Processing volumes
   - Success rates
   - Data quality metrics
   - Cost tracking

3. **Debug Dashboard**
   - Detailed error logs
   - Performance traces
   - Resource metrics
   - Cache statistics

## Metric Collection

### Using the MetricsEmitter

```python
from utils.metrics_emitter import MetricsEmitter

metrics = MetricsEmitter(service="github-scraper")

# Track operation
metrics.track_duration(
    operation="fetch_contributors",
    duration=123.45,
    resource="openai/gpt-3"
)

# Track success/failure
metrics.track_success(
    operation="profile_match",
    resource="user123"
)

# Track batch operations
metrics.track_batch_operation(
    operation="process_profiles",
    total=100,
    successful=95,
    resource="github_batch"
)
```
