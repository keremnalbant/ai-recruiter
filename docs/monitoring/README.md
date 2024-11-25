# Monitoring and Observability Guide

## Overview
This guide details the comprehensive monitoring and observability setup for the GitHub LinkedIn Analyzer system, including metrics, logging, alerting, and debugging capabilities.

## Quick Start

### 1. Deploy Monitoring Infrastructure
```bash
# Deploy monitoring for development
python scripts/deploy_monitoring.py --environment dev

# Deploy monitoring for production
python scripts/deploy_monitoring.py --environment prod
```

### 2. Access Monitoring Tools
- CloudWatch Dashboard: `https://<region>.console.aws.amazon.com/cloudwatch/home#dashboards:name=github-linkedin-analyzer-<env>`
- Logs: CloudWatch Logs Groups under `/aws/lambda/github-linkedin-analyzer-<env>-*`
- Metrics: Namespace `GitHubLinkedInAnalyzer`
- Traces: AWS X-Ray traces
- Alerts: SNS Topic `github-linkedin-analyzer-<env>-alerts`

## Components

### 1. Metrics Collection
- **Lambda Powertools Metrics**
  - Automatic Lambda metrics
  - Custom business metrics
  - Detailed performance metrics
  
- **CloudWatch Custom Metrics**
  - API performance
  - Scraping success rates
  - Cache efficiency
  - State transitions

### 2. Logging System
- **Structured Logging**
  - JSON format
  - Correlation IDs
  - Request tracking
  
- **Log Levels**
  - Production: INFO and above
  - Development: DEBUG and above
  - Error tracking: All levels

### 3. Alerting System
- **SNS Notifications**
  - Email alerts
  - Slack integration
  - PagerDuty/OpsGenie integration
  
- **Alert Categories**
  - Critical (P1): Immediate action required
  - Warning (P2): Investigation needed
  - Info (P3): Awareness only

## Dashboards

### 1. Main Dashboard
- System health overview
- Key performance indicators
- Error rates and latencies
- Resource utilization

### 2. Debug Dashboard
- Detailed error logs
- Performance traces
- Cache statistics
- Rate limit tracking

## Alert Configuration

### 1. Production Thresholds
```yaml
APIErrors:
  threshold: 3
  period: 300
  evaluation_periods: 2
  
APILatency:
  threshold: 2000  # ms
  period: 300
  evaluation_periods: 2

RateLimit:
  threshold: 500
  period: 60
  evaluation_periods: 1
```

### 2. Development Thresholds
```yaml
APIErrors:
  threshold: 5
  period: 300
  evaluation_periods: 2
  
APILatency:
  threshold: 5000  # ms
  period: 300
  evaluation_periods: 2

RateLimit:
  threshold: 100
  period: 60
  evaluation_periods: 1
```

## Debugging Tools

### 1. Log Insights Queries
Pre-built queries available in `resources/cloudwatch/log_queries.yaml`:
- API error analysis
- Latency patterns
- Scraping performance
- State transitions
- Cold start analysis

### 2. X-Ray Traces
- End-to-end request tracking
- Performance bottleneck identification
- Error chain analysis
- Service map visualization

## Common Operations

### 1. Investigating Issues
```bash
# 1. Check alarms
aws cloudwatch describe-alarms \
  --alarm-names "github-linkedin-analyzer-*" \
  --state-value ALARM

# 2. View recent errors
aws logs insights-query \
  --log-group-name "/aws/lambda/github-linkedin-analyzer-prod-*" \
  --query-string "$(cat resources/cloudwatch/log_queries.yaml | yq .ErrorPatterns.query)"

# 3. Analyze performance
aws cloudwatch get-metric-data \
  --metric-data-queries file://resources/cloudwatch/performance_query.json \
  --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
  --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ")
```

### 2. Performance Optimization
1. Monitor cold starts:
   ```bash
   aws logs insights-query \
     --query-string "$(cat resources/cloudwatch/log_queries.yaml | yq .ColdStarts.query)"
   ```

2. Check cache efficiency:
   ```bash
   aws logs insights-query \
     --query-string "$(cat resources/cloudwatch/log_queries.yaml | yq .CacheEfficiency.query)"
   ```

### 3. Cost Optimization
1. Monitor Lambda duration:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --statistics Average Maximum \
     --period 3600
   ```

2. Track API usage:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace GitHubLinkedInAnalyzer \
     --metric-name APIRequests \
     --statistics Sum \
     --period 86400
   ```

## Best Practices

### 1. Monitoring
- Use structured logging
- Include correlation IDs
- Set appropriate thresholds
- Monitor trends, not just points
- Use composite alarms for complex scenarios

### 2. Alerting
- Configure proper severity levels
- Set up escalation policies
- Include runbooks in alerts
- Avoid alert fatigue
- Test alert paths regularly

### 3. Debugging
- Use correlation IDs
- Follow error chains
- Check multiple time windows
- Compare with baseline
- Document findings

## Maintenance

### 1. Regular Tasks
- Review and adjust thresholds
- Archive old logs
- Update dashboards
- Test alerting paths
- Clean up old alarms

### 2. Incident Response
- Follow runbooks
- Document actions
- Update monitoring
- Conduct post-mortems
- Implement improvements

## Integration

### 1. CI/CD Pipeline
- Deploy monitoring with infrastructure
- Test alerts in staging
- Validate dashboards
- Check metric emission

### 2. Development Workflow
- Local metric emission
- Log level configuration
- Debug mode settings
- Test coverage for monitoring

## Additional Resources
- [Metrics Reference](./metrics_reference.md)
- [Alert Runbooks](./runbooks/)
- [Dashboard Templates](./dashboards/)
- [Query Library](./queries/)
