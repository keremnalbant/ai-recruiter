import json
import os
from datetime import datetime
from typing import Any, Dict, List

import boto3
import requests
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
SEVERITY_COLORS = {
    "ALARM": "#FF0000",      # Red
    "OK": "#36A64F",         # Green
    "INSUFFICIENT_DATA": "#DAA520"  # GoldenRod
}

def format_alarm_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Format CloudWatch alarm for Slack."""
    alarm_data = json.loads(message["Message"])
    
    # Extract alarm details
    alarm_name = alarm_data["AlarmName"]
    alarm_description = alarm_data.get("AlarmDescription", "No description")
    new_state = alarm_data["NewStateValue"]
    reason = alarm_data["NewStateReason"]
    timestamp = datetime.fromtimestamp(alarm_data["StateChangeTime"]/1000.0)
    
    # Format blocks for Slack message
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 CloudWatch Alarm: {alarm_name}"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Status:*\n{new_state}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{alarm_description}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Reason:*\n{reason}"
            }
        }
    ]
    
    # Add metrics if available
    if "Trigger" in alarm_data:
        trigger = alarm_data["Trigger"]
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Metric:*\n{trigger['MetricName']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Namespace:*\n{trigger['Namespace']}"
                }
            ]
        })
    
    # Add actions based on severity
    if new_state == "ALARM":
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "👉 *Actions Required:*\n• Check CloudWatch logs\n• Review metrics dashboard\n• Check system health"
            }
        })
    
    return {
        "attachments": [
            {
                "color": SEVERITY_COLORS.get(new_state, "#000000"),
                "blocks": blocks
            }
        ]
    }

def send_to_slack(message: Dict[str, Any]) -> None:
    """Send formatted message to Slack."""
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info("Successfully sent message to Slack")
        
        # Track successful notification
        metrics.add_metric(
            name="SlackNotificationsSent",
            unit="Count",
            value=1
        )
    except Exception as e:
        logger.error(f"Failed to send message to Slack: {str(e)}")
        metrics.add_metric(
            name="SlackNotificationErrors",
            unit="Count",
            value=1
        )
        raise

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Handle SNS notifications and forward to Slack."""
    try:
        logger.info("Processing SNS notification", extra={"event": event})
        
        # Process each record
        for record in event["Records"]:
            if record["EventSource"] != "aws:sns":
                logger.warning(f"Skipping non-SNS event: {record['EventSource']}")
                continue
            
            # Format and send message
            message = format_alarm_message(record["Sns"])
            send_to_slack(message)
        
        return {
            "statusCode": 200,
            "body": "Successfully processed notifications"
        }
        
    except Exception as e:
        logger.exception("Error processing notification")
        return {
            "statusCode": 500,
            "body": f"Error processing notification: {str(e)}"
        }
