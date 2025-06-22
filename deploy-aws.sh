#!/bin/bash

# AWS Deployment Script for LLM Inference Stress Testing Tool
# Choose your deployment method below

set -e

echo "🚀 AWS Deployment Options for LLM Inference Stress Testing Tool"
echo "================================================================"
echo ""
echo "1. AWS App Runner (Recommended - Easiest)"
echo "2. AWS ECS with Fargate"
echo "3. AWS EC2 with Docker"
echo "4. AWS Lambda + API Gateway (Serverless)"
echo ""

read -p "Choose deployment option (1-4): " choice

case $choice in
    1)
        echo "🏃 Deploying with AWS App Runner..."
        
        # Check if AWS CLI is installed
        if ! command -v aws &> /dev/null; then
            echo "❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/"
            exit 1
        fi
        
        # Check if GitHub repo is set up
        echo "📋 Prerequisites for App Runner:"
        echo "1. Push your code to GitHub"
        echo "2. Set environment variables in App Runner console:"
        echo "   - OPENAI_API_KEY"
        echo "   - ANTHROPIC_API_KEY (optional)"
        echo "   - GOOGLE_API_KEY (optional)"
        echo ""
        echo "🌐 After deployment, go to AWS Console > App Runner > Create Service"
        echo "   - Source: GitHub repository"
        echo "   - Runtime: Docker"
        echo "   - Build file: apprunner.yaml"
        echo ""
        ;;
        
    2)
        echo "🐳 Deploying with AWS ECS + Fargate..."
        
        # Build and push to ECR
        AWS_REGION=$(aws configure get region || echo "us-east-1")
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        ECR_REPO="llm-infer-stress"
        
        echo "Creating ECR repository..."
        aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION || true
        
        echo "Building Docker image..."
        docker build -t $ECR_REPO .
        
        echo "Logging into ECR..."
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
        
        echo "Tagging and pushing image..."
        docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
        docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
        
        echo "✅ Image pushed to ECR!"
        echo "🌐 Now create ECS service in AWS Console with this image:"
        echo "   $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"
        ;;
        
    3)
        echo "🖥️  EC2 Deployment Instructions:"
        echo "1. Launch EC2 instance (t3.medium recommended)"
        echo "2. Install Docker:"
        echo "   sudo yum update -y"
        echo "   sudo yum install -y docker"
        echo "   sudo systemctl start docker"
        echo "   sudo usermod -a -G docker ec2-user"
        echo ""
        echo "3. Copy this project to EC2 and run:"
        echo "   docker build -t llm-infer-stress ."
        echo "   docker run -d -p 80:8501 llm-infer-stress"
        ;;
        
    4)
        echo "⚡ Serverless deployment requires code modifications for Lambda"
        echo "Consider using Streamlit Cloud or App Runner for Streamlit apps"
        ;;
        
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "📋 Don't forget to set environment variables:"
echo "- OPENAI_API_KEY=your_openai_key"
echo "- ANTHROPIC_API_KEY=your_anthropic_key (optional)"
echo "- GOOGLE_API_KEY=your_google_key (optional)"
echo ""
echo "🎉 Deployment script completed!" 