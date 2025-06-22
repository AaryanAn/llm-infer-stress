#!/bin/bash

# Setup IAM Roles for App Runner Deployment
# This script creates the necessary IAM roles and policies

set -e

echo "🔐 Setting up IAM Roles for App Runner..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is configured with basic credentials
echo "📋 Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. You need basic credentials first.${NC}"
    echo "Run: aws configure"
    echo "Enter temporary access keys, we'll replace with roles after setup."
    exit 1
fi

# Get current AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${GREEN}✅ AWS Account ID: $AWS_ACCOUNT_ID${NC}"
echo -e "${GREEN}✅ AWS Region: $AWS_REGION${NC}"

# Create IAM policies
echo ""
echo "📝 Creating IAM policies..."

# App Runner Instance Role Policy
echo "Creating App Runner instance policy..."
aws iam create-policy \
    --policy-name LLMInferStressAppRunnerInstancePolicy \
    --policy-document file://app-runner-instance-role-policy.json \
    --description "Policy for LLM Infer Stress App Runner instance" \
    2>/dev/null || echo "Policy already exists"

# App Runner Access Role Policy  
echo "Creating App Runner access policy..."
aws iam create-policy \
    --policy-name LLMInferStressAppRunnerAccessPolicy \
    --policy-document file://app-runner-access-role-policy.json \
    --description "Policy for LLM Infer Stress App Runner access" \
    2>/dev/null || echo "Policy already exists"

# Create IAM roles
echo ""
echo "👤 Creating IAM roles..."

# App Runner Instance Role
echo "Creating App Runner instance role..."
aws iam create-role \
    --role-name LLMInferStressAppRunnerInstanceRole \
    --assume-role-policy-document file://app-runner-instance-trust-policy.json \
    --description "Instance role for LLM Infer Stress App Runner service" \
    2>/dev/null || echo "Role already exists"

# App Runner Access Role
echo "Creating App Runner access role..."
aws iam create-role \
    --role-name LLMInferStressAppRunnerAccessRole \
    --assume-role-policy-document file://app-runner-access-trust-policy.json \
    --description "Access role for LLM Infer Stress App Runner service" \
    2>/dev/null || echo "Role already exists"

# Attach policies to roles
echo ""
echo "🔗 Attaching policies to roles..."

# Attach instance policy
aws iam attach-role-policy \
    --role-name LLMInferStressAppRunnerInstanceRole \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/LLMInferStressAppRunnerInstancePolicy

# Attach access policy
aws iam attach-role-policy \
    --role-name LLMInferStressAppRunnerAccessRole \
    --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/LLMInferStressAppRunnerAccessPolicy

echo ""
echo -e "${GREEN}🎉 IAM Roles created successfully!${NC}"
echo ""
echo "📋 Role ARNs:"
echo -e "${YELLOW}Instance Role:${NC} arn:aws:iam::$AWS_ACCOUNT_ID:role/LLMInferStressAppRunnerInstanceRole"
echo -e "${YELLOW}Access Role:${NC} arn:aws:iam::$AWS_ACCOUNT_ID:role/LLMInferStressAppRunnerAccessRole"
echo ""
echo -e "${GREEN}✅ Ready for App Runner deployment!${NC}"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Create App Runner service using these roles"
echo "3. Set environment variables in App Runner console" 