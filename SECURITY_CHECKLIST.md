# 🔒 Security Checklist for AWS Deployment

## ✅ Pre-Deployment Security Verification

### **1. Credential Protection**
- [ ] No API keys in source code
- [ ] No AWS credentials in git repository
- [ ] No secrets in Docker images
- [ ] Environment variables used for all sensitive data

### **2. Git Repository Security**
- [ ] `.gitignore` properly configured
- [ ] No sensitive files committed
- [ ] API keys removed from commit history
- [ ] Personal files excluded

### **3. Docker Security**
- [ ] `.dockerignore` configured
- [ ] No credentials in Docker layers
- [ ] Minimal base image used
- [ ] No unnecessary files in container

### **4. AWS IAM Security**
- [ ] Least privilege principle applied
- [ ] Proper IAM roles created
- [ ] No hardcoded AWS credentials
- [ ] Role-based access implemented

## 🚨 **CRITICAL: Files That Must NEVER Be Committed**

### **API Keys & Tokens**
```
❌ NEVER COMMIT:
- OpenAI API keys (sk-proj-...)
- Anthropic API keys (sk-ant-...)
- Google API keys
- Any *_API_KEY variables
- JWT tokens
- Session tokens
```

### **AWS Credentials**
```
❌ NEVER COMMIT:
- AWS Access Keys (AKIA...)
- AWS Secret Keys
- .aws/credentials file
- .aws/config file
- IAM user credentials
- Temporary credentials
```

### **Personal Information**
```
❌ NEVER COMMIT:
- Resume files
- Personal documents
- Private configuration files
- Local development settings
```

## 🔧 **Security Best Practices**

### **Environment Variables**
```bash
# ✅ CORRECT: Use environment variables
export OPENAI_API_KEY="your_key_here"
export ANTHROPIC_API_KEY="your_key_here"

# ❌ WRONG: Hardcoded in code
openai_key = "sk-proj-actual-key-here"
```

### **Docker Environment**
```dockerfile
# ✅ CORRECT: Use build args and env vars
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# ❌ WRONG: Hardcoded in Dockerfile
ENV OPENAI_API_KEY="sk-proj-actual-key-here"
```

### **AWS App Runner**
```yaml
# ✅ CORRECT: Set in App Runner console
# Environment Variables section:
# OPENAI_API_KEY = your_actual_key

# ❌ WRONG: In apprunner.yaml
env:
  - name: OPENAI_API_KEY
    value: "sk-proj-actual-key-here"
```

## 🛡️ **Security Verification Commands**

### **Check for exposed secrets**
```bash
# Search for potential API keys
grep -r "sk-" . --exclude-dir=.git --exclude-dir=.venv*
grep -r "AKIA" . --exclude-dir=.git --exclude-dir=.venv*

# Check git history for secrets
git log --grep="key\|secret\|password" -i

# Verify .gitignore is working
git status --ignored
```

### **Docker security check**
```bash
# Build and inspect image
docker build -t security-check .
docker run --rm security-check find / -name "*key*" -o -name "*secret*" 2>/dev/null
```

## 🚨 **If You Accidentally Committed Secrets**

### **Immediate Actions**
1. **Revoke the exposed credentials immediately**
2. **Generate new API keys**
3. **Remove from git history:**
```bash
# Remove file from git history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secret/file' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (DANGEROUS - only for personal repos)
git push origin --force --all
```

### **OpenAI API Key Exposed**
1. Go to: https://platform.openai.com/api-keys
2. Delete the exposed key
3. Create a new key
4. Update App Runner environment variables

### **AWS Credentials Exposed**
1. Go to: https://console.aws.amazon.com/iam/
2. Delete the exposed access key
3. Create new access key
4. Update local AWS configuration

## ✅ **Current Security Status**

### **Protected Files**
- [x] `.gitignore` configured for secrets
- [x] `.dockerignore` prevents credential inclusion
- [x] AWS IAM roles properly configured
- [x] API keys removed from documentation

### **Environment Variables Required**
```
OPENAI_API_KEY=your_actual_openai_key
ANTHROPIC_API_KEY=your_actual_anthropic_key (optional)
GOOGLE_API_KEY=your_actual_google_key (optional)
```

### **AWS Roles Created**
- [x] Instance Role: `LLMInferStressAppRunnerInstanceRole`
- [x] Access Role: `LLMInferStressAppRunnerAccessRole`

## 📋 **Pre-Deployment Checklist**

Before deploying to AWS App Runner:

1. [ ] Run security verification commands
2. [ ] Confirm no secrets in git repository
3. [ ] Verify environment variables are set correctly
4. [ ] Test Docker build excludes sensitive files
5. [ ] IAM roles properly configured
6. [ ] API keys are valid and active

---

**Remember: Security is not optional - it's essential!** 