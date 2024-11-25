from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
    aws_lambda_python_alpha as lambda_python
)
from constructs import Construct
from typing import Any, Dict


class GithubLinkedInAnalyzerStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)

        # DynamoDB Tables
        # State Management Table
        state_table = dynamodb.Table(
            self, "StateTable",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

        # Profile Cache Table
        cache_table = dynamodb.Table(
            self, "ProfileCache",
            partition_key=dynamodb.Attribute(
                name="profile_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="ttl",
        )

        # Lambda Layer for Common Dependencies
        common_layer = lambda_python.PythonLayerVersion(
            self, "CommonLayer",
            entry="layers/common",
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Lambda Functions
        # API Handler
        api_handler = lambda_python.PythonFunction(
            self, "APIHandler",
            entry="lambda/api",
            index="handler.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.seconds(30),
            memory_size=1024,
            layers=[common_layer],
            environment={
                "STATE_TABLE": state_table.table_name,
                "CACHE_TABLE": cache_table.table_name,
                "GITHUB_TOKEN": "{{resolve:ssm:/github-linkedin-analyzer/github-token}}",
                "ANTHROPIC_API_KEY": "{{resolve:ssm:/github-linkedin-analyzer/anthropic-key}}",
            },
        )

        # GitHub Scraper
        github_scraper = lambda_python.PythonFunction(
            self, "GitHubScraper",
            entry="lambda/github_scraper",
            index="handler.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.minutes(5),
            memory_size=1024,
            layers=[common_layer],
            environment={
                "STATE_TABLE": state_table.table_name,
                "CACHE_TABLE": cache_table.table_name,
                "GITHUB_TOKEN": "{{resolve:ssm:/github-linkedin-analyzer/github-token}}",
            },
        )

        # LinkedIn Scraper
        linkedin_scraper = lambda_python.PythonFunction(
            self, "LinkedInScraper",
            entry="lambda/linkedin_scraper",
            index="handler.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.minutes(5),
            memory_size=2048,
            layers=[common_layer],
            environment={
                "STATE_TABLE": state_table.table_name,
                "CACHE_TABLE": cache_table.table_name,
                "LINKEDIN_EMAIL": "{{resolve:ssm:/github-linkedin-analyzer/linkedin-email}}",
                "LINKEDIN_PASSWORD": "{{resolve:ssm:/github-linkedin-analyzer/linkedin-password}}",
            },
        )

        # State Manager
        state_manager = lambda_python.PythonFunction(
            self, "StateManager",
            entry="lambda/state_manager",
            index="handler.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.seconds(30),
            memory_size=512,
            layers=[common_layer],
            environment={
                "STATE_TABLE": state_table.table_name,
            },
        )

        # Grant permissions
        state_table.grant_read_write_data(api_handler)
        state_table.grant_read_write_data(github_scraper)
        state_table.grant_read_write_data(linkedin_scraper)
        state_table.grant_read_write_data(state_manager)
        
        cache_table.grant_read_write_data(api_handler)
        cache_table.grant_read_write_data(github_scraper)
        cache_table.grant_read_write_data(linkedin_scraper)

        # API Gateway
        api = apigw.RestApi(
            self, "GithubLinkedInAnalyzerAPI",
            rest_api_name="Github LinkedIn Analyzer API",
            description="Serverless API for analyzing GitHub and LinkedIn profiles",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )

        # API Gateway Integration
        api_integration = apigw.LambdaIntegration(
            api_handler,
            proxy=True,
            integration_responses=[
                apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": "'*'",
                    },
                )
            ],
        )

        api.root.add_method(
            "POST",
            api_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )


app = App()
GithubLinkedInAnalyzerStack(app, "GithubLinkedInAnalyzerStack")
app.synth()
