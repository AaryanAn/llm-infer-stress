# 🚀 AWS App Runner Deployment Guide

## ✅ Prerequisites Completed
- [x] IAM Roles created with proper permissions
- [x] Code pushed to GitHub: https://github.com/AaryanAn/llm-infer-stress
- [x] Dockerfile and apprunner.yaml configured

## 📋 IAM Roles Created
- **Instance Role**: `arn:aws:iam::628532653431:role/LLMInferStressAppRunnerInstanceRole`
- **Access Role**: `arn:aws:iam::628532653431:role/LLMInferStressAppRunnerAccessRole`

## 🎯 Step-by-Step Deployment

### Step 1: Open AWS App Runner Console
1. Go to: https://console.aws.amazon.com/apprunner/
2. Make sure you're in **us-east-1** region (top right)
3. Click **"Create service"**

### Step 2: Configure Source
1. **Source type**: Repository
2. **Repository provider**: GitHub
3. **Connect to GitHub**: 
   - Click "Add new" if not connected
   - Authorize AWS to access your GitHub
4. **Repository**: Select `AaryanAn/llm-infer-stress`
5. **Branch**: `main`
6. **Deployment trigger**: Automatic (deploys on push)

### Step 3: Configure Build
1. **Configuration file**: Use configuration file
2. **Configuration file**: `apprunner.yaml` (should auto-detect)

### Step 4: Configure Service
1. **Service name**: `llm-infer-stress-app`
2. **Virtual CPU**: 1 vCPU
3. **Memory**: 2 GB
4. **Environment variables** (click "Add environment variable"):
   ```
   OPENAI_API_KEY = your_openai_api_key_here
   ANTHROPIC_API_KEY = your_anthropic_api_key_here (optional)
   GOOGLE_API_KEY = your_google_api_key_here (optional)
   ```
   
   ⚠️ **SECURITY NOTE**: Use your actual API keys here, but NEVER commit them to git!

### Step 5: Configure Security (IAM Roles)
1. **Instance role**: Select existing role
   - Choose: `LLMInferStressAppRunnerInstanceRole`
2. **Access role**: Select existing role  
   - Choose: `LLMInferStressAppRunnerAccessRole`

### Step 6: Configure Networking (Optional)
1. **Incoming traffic**: Public endpoint
2. **Outgoing traffic**: Allow all

### Step 7: Configure Observability
1. **AWS X-Ray tracing**: Enable (recommended)
2. **Configuration source**: Default

### Step 8: Review and Create
1. Review all settings
2. Click **"Create & deploy"**

## ⏱️ Deployment Timeline
- **Creation**: 5-10 minutes
- **Build**: 10-15 minutes  
- **Deploy**: 5 minutes
- **Total**: ~20-30 minutes

## 🌐 After Deployment
1. **Service URL**: You'll get a URL like: `https://xyz123.us-east-1.awsapprunner.com`
2. **Custom domain**: You can add your own domain later
3. **HTTPS**: Automatically enabled with SSL certificate

## 📊 Monitoring Your App
1. **App Runner Console**: Real-time logs and metrics
2. **CloudWatch**: Detailed monitoring and alerts
3. **Your App**: Built-in Prometheus metrics at `/metrics`

## 💰 Cost Estimate
- **App Runner**: ~$7-15/month for basic usage
- **Data transfer**: Minimal for testing
- **CloudWatch logs**: ~$1-2/month

## 🔧 Troubleshooting

### Build Fails
- Check GitHub connection
- Verify `apprunner.yaml` syntax
- Check Docker build logs in console

### App Won't Start
- Verify environment variables
- Check application logs in App Runner console
- Ensure port 8501 is exposed

### IAM Issues
- Verify roles are attached correctly
- Check trust relationships
- Ensure policies have correct permissions

## 🎉 Success!
Once deployed, your LLM stress testing tool will be live at your App Runner URL!

**Features available:**
- ✅ Streamlit dashboard
- ✅ Real-time stress testing
- ✅ Prometheus metrics
- ✅ Professional UI
- ✅ Automatic scaling
- ✅ HTTPS enabled

## 🔄 Updates
To update your app:
1. Push changes to GitHub `main` branch
2. App Runner automatically rebuilds and deploys
3. Zero downtime deployment

---

**Need help?** Check the AWS App Runner documentation or contact support. 