#!/usr/bin/env python3
import argparse
import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

class MonitoringDeployer:
    """Deploy monitoring infrastructure based on environment configuration."""
    
    def __init__(self, environment: str, region: str):
        self.environment = environment
        self.config = self._load_config(environment)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.cloudformation = boto3.client('cloudformation', region_name=region)
    
    def _load_config(self, environment: str) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        config_path = f"config/monitoring/{environment}.json"
        if not os.path.exists(config_path):
            raise ValueError(f"Configuration not found for environment: {environment}")
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def deploy_dashboard(self) -> None:
        """Deploy CloudWatch dashboard."""
        try:
            dashboard_name = f"github-linkedin-analyzer-{self.environment}"
            
            # Load dashboard template
            with open('resources/cloudwatch/dashboard.json', 'r') as f:
                dashboard_body = f.read()
            
            # Replace placeholders with actual values
            dashboard_body = dashboard_body.replace(
                "${Environment}",
                self.environment
            )
            
            # Create/update dashboard
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=dashboard_body
            )
            print(f"Successfully deployed dashboard: {dashboard_name}")
            
        except Exception as e:
            print(f"Error deploying dashboard: {e}")
            raise
    
    def update_alarms(self) -> None:
        """Update CloudWatch alarms based on environment configuration."""
        try:
            alarm_config = self.config["Parameters"]["MetricsConfiguration"]["Alarms"]
            
            for alarm_name, settings in alarm_config.items():
                alarm_prefix = f"github-linkedin-analyzer-{self.environment}"
                full_alarm_name = f"{alarm_prefix}-{alarm_name}"
                
                # Create/update alarm
                self.cloudwatch.put_metric_alarm(
                    AlarmName=full_alarm_name,
                    AlarmDescription=f"{alarm_name} for {self.environment}",
                    ActionsEnabled=True,
                    MetricName=settings.get("MetricName", alarm_name),
                    Namespace="GitHubLinkedInAnalyzer",
                    Statistic="Sum",
                    Period=settings["Period"],
                    EvaluationPeriods=settings["EvaluationPeriods"],
                    Threshold=settings["Threshold"],
                    ComparisonOperator="GreaterThanThreshold",
                    TreatMissingData="notBreaching"
                )
                print(f"Successfully updated alarm: {full_alarm_name}")
                
        except Exception as e:
            print(f"Error updating alarms: {e}")
            raise
    
    def setup_notifications(self) -> None:
        """Set up SNS topics and subscriptions."""
        try:
            topic_name = f"github-linkedin-analyzer-{self.environment}-alerts"
            
            # Create SNS topic
            topic_response = self.sns.create_topic(Name=topic_name)
            topic_arn = topic_response['TopicArn']
            
            # Add email subscription
            self.sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=self.config["Parameters"]["AlarmEmail"]
            )
            
            # Add HTTPS subscription for webhook
            if webhook_url := self.config["Parameters"].get("AlertWebhookUrl"):
                self.sns.subscribe(
                    TopicArn=topic_arn,
                    Protocol='https',
                    Endpoint=webhook_url
                )
            
            print(f"Successfully set up notifications for {topic_name}")
            
        except Exception as e:
            print(f"Error setting up notifications: {e}")
            raise
    
    def configure_log_groups(self) -> None:
        """Configure CloudWatch Log Groups."""
        try:
            logs = boto3.client('logs')
            retention_days = self.config["Parameters"]["Logging"]["RetentionDays"]
            
            # Set retention for Lambda function logs
            function_names = [
                "APIFunction",
                "GitHubScraperFunction",
                "LinkedInScraperFunction",
                "StateManagerFunction"
            ]
            
            for function in function_names:
                log_group = f"/aws/lambda/github-linkedin-analyzer-{self.environment}-{function}"
                try:
                    logs.put_retention_policy(
                        logGroupName=log_group,
                        retentionInDays=retention_days
                    )
                    print(f"Set retention policy for {log_group}")
                except ClientError as e:
                    if e.response['Error']['Code'] != 'ResourceNotFoundException':
                        raise
                    
        except Exception as e:
            print(f"Error configuring log groups: {e}")
            raise
    
    def deploy_all(self) -> None:
        """Deploy all monitoring components."""
        print(f"Deploying monitoring for environment: {self.environment}")
        
        self.deploy_dashboard()
        self.update_alarms()
        self.setup_notifications()
        self.configure_log_groups()
        
        print("Monitoring deployment completed successfully")


def main():
    parser = argparse.ArgumentParser(description='Deploy monitoring infrastructure')
    parser.add_argument('--environment', '-e', required=True, choices=['dev', 'prod'],
                       help='Environment to deploy')
    parser.add_argument('--region', '-r', default='us-east-1',
                       help='AWS region')
    
    args = parser.parse_args()
    
    deployer = MonitoringDeployer(args.environment, args.region)
    deployer.deploy_all()


if __name__ == '__main__':
    main()
