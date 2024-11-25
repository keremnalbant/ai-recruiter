#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

def get_ssm_parameters(environment: str) -> Dict[str, str]:
    """Get parameters from SSM Parameter Store."""
    ssm = boto3.client('ssm')
    parameters = {
        'github-token': f'/{environment}/github-linkedin-analyzer/github-token',
        'anthropic-key': f'/{environment}/github-linkedin-analyzer/anthropic-key',
        'linkedin-email': f'/{environment}/github-linkedin-analyzer/linkedin-email',
        'linkedin-password': f'/{environment}/github-linkedin-analyzer/linkedin-password'
    }
    
    values = {}
    try:
        for key, param_name in parameters.items():
            response = ssm.get_parameter(Name=param_name, WithDecryption=True)
            values[key] = response['Parameter']['Value']
    except ClientError as e:
        print(f"Error getting SSM parameters: {e}")
        raise
    
    return values

def update_env_file(environment: str, parameters: Dict[str, str]) -> None:
    """Update .env file with parameters."""
    env_content = [
        f"ENVIRONMENT={environment}",
        f"GITHUB_TOKEN={parameters['github-token']}",
        f"ANTHROPIC_API_KEY={parameters['anthropic-key']}",
        f"LINKEDIN_EMAIL={parameters['linkedin-email']}",
        f"LINKEDIN_PASSWORD={parameters['linkedin-password']}"
    ]
    
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))

def build_layer(layer_dir: str) -> None:
    """Build Lambda layer."""
    requirements_file = os.path.join(layer_dir, 'requirements.txt')
    if not os.path.exists(requirements_file):
        print(f"No requirements.txt found in {layer_dir}")
        return
    
    print(f"Building layer in {layer_dir}")
    subprocess.run([
        'pip', 'install',
        '-r', requirements_file,
        '-t', os.path.join(layer_dir, 'python'),
        '--platform', 'manylinux2014_x86_64',
        '--only-binary=:all:'
    ], check=True)

def run_tests() -> bool:
    """Run pytest and return True if all tests pass."""
    result = subprocess.run(['pytest', '-v'], capture_output=True)
    return result.returncode == 0

def package_application(
    template_file: str,
    s3_bucket: str,
    environment: str
) -> str:
    """Package SAM application."""
    output_template = f'packaged-{environment}.yaml'
    subprocess.run([
        'sam', 'package',
        '--template-file', template_file,
        '--s3-bucket', s3_bucket,
        '--output-template-file', output_template
    ], check=True)
    return output_template

def deploy_application(
    template_file: str,
    stack_name: str,
    environment: str,
    parameters: Optional[List[str]] = None
) -> None:
    """Deploy SAM application."""
    command = [
        'sam', 'deploy',
        '--template-file', template_file,
        '--stack-name', stack_name,
        '--capabilities', 'CAPABILITY_IAM',
        '--parameter-overrides',
        f'Environment={environment}'
    ]
    
    if parameters:
        command.extend(parameters)
    
    subprocess.run(command, check=True)

def main() -> None:
    parser = argparse.ArgumentParser(description='Deploy GitHub LinkedIn Analyzer')
    parser.add_argument('--environment', choices=['dev', 'prod'], required=True)
    parser.add_argument('--s3-bucket', required=True)
    parser.add_argument('--skip-tests', action='store_true')
    args = parser.parse_args()

    # Set environment variables
    os.environ['AWS_SAM_STACK_NAME'] = f'github-linkedin-analyzer-{args.environment}'

    try:
        # Get parameters from SSM
        print("Getting parameters from SSM...")
        parameters = get_ssm_parameters(args.environment)
        
        # Update .env file
        print("Updating .env file...")
        update_env_file(args.environment, parameters)
        
        # Build layers
        print("Building Lambda layers...")
        build_layer('layers/common')
        
        # Run tests
        if not args.skip_tests:
            print("Running tests...")
            if not run_tests():
                print("Tests failed. Aborting deployment.")
                return
        
        # Package application
        print("Packaging application...")
        packaged_template = package_application(
            'template.yaml',
            args.s3_bucket,
            args.environment
        )
        
        # Deploy application
        print("Deploying application...")
        deploy_application(
            packaged_template,
            os.environ['AWS_SAM_STACK_NAME'],
            args.environment
        )
        
        print("Deployment completed successfully!")

    except Exception as e:
        print(f"Error during deployment: {e}")
        raise

if __name__ == '__main__':
    main()
