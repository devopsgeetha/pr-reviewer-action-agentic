# Deployment Guide

This guide covers multiple deployment options for making your AI PR Reviewer Bot available to other repositories and users.

## Table of Contents

- [Option 1: GitHub Action (Recommended for Quick Adoption)](#option-1-github-action)
- [Option 2: Docker Container (Self-Hosting)](#option-2-docker-container)
- [Option 3: GitHub App (Enterprise/Multi-Tenant)](#option-3-github-app)
- [Option 4: CLI Tool (Local Development)](#option-4-cli-tool)
- [Option 5: SaaS Platform (Commercial)](#option-5-saas-platform)
- [Cloud Deployment Options](#cloud-deployment-options)

---

## Option 1: GitHub Action

**Best for:** Quick adoption, easy user onboarding, no infrastructure management

### Advantages
- ✅ Users install with 3 lines of YAML
- ✅ No server infrastructure needed
- ✅ Automatic updates via version tags
- ✅ Works with any GitHub repository
- ✅ Free for public repos

### Disadvantages
- ❌ Runs on every PR (GitHub Actions minutes usage)
- ❌ Limited to GitHub only (no GitLab support)
- ❌ Cold start times on first run

### Setup Instructions

1. **Create Action Files** (already created):
   - `action.yml` - Action metadata
   - `Dockerfile.action` - Container definition
   - `action-entrypoint.sh` - Execution script

2. **Create New Repository**:
   ```bash
   # Create a new repo on GitHub: pr-reviewer-action
   git clone https://github.com/yourusername/pr-reviewer-action.git
   cd pr-reviewer-action
   
   # Copy action files
   cp action.yml Dockerfile.action action-entrypoint.sh ACTION_README.md pr-reviewer-action/
   cp -r backend/ pr-reviewer-action/
   ```

3. **Test Locally** (optional):
   ```bash
   # Install 'act' tool for local testing
   # Windows (using winget):
   winget install nektos.act
   
   # Windows (using Scoop):
   scoop install act
   
   # Windows (manual - download from GitHub):
   # Download from https://github.com/nektos/act/releases
   # Extract and add to PATH
   
   # Mac: brew install act
   # Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   
   # Test the action locally (run from project root):
   # Make sure you're in the Capstone_Project directory
   cd C:\Software\Capstone_Project
   
   # Run act with the test workflow
   act pull_request -W .github/workflows/test-action.yml -s OPENAI_API_KEY=your-key -s GITHUB_TOKEN=your-token
   
   # Or list available workflows:
   act -l
   ```
   
   **Note**: The test workflow (`.github/workflows/test-action.yml`) uses the local action (`.`), so it will test your action from the current directory.

4. **Publish to GitHub**:
   ```bash
   cd pr-reviewer-action
   git add .
   git commit -m "Initial action release"
   git tag -a v1 -m "Version 1.0"
   git push origin main
   git push origin v1
   ```

5. **Users Can Now Use It**:
   ```yaml
   # In any repo: .github/workflows/pr-review.yml
   name: AI Code Review
   on: [pull_request]
   
   jobs:
     review:
       runs-on: ubuntu-latest
       steps:
         - uses: yourusername/pr-reviewer-action@v1
           with:
             openai_api_key: ${{ secrets.OPENAI_API_KEY }}
   ```

6. **Publish to Marketplace** (optional):
   - Go to your action repo on GitHub
   - Click "Draft a release"
   - Check "Publish to GitHub Marketplace"
   - Fill in details and publish

### Cost Considerations
- GitHub Actions: 2,000 free minutes/month (public repos unlimited)
- OpenAI API: ~$0.01-0.03 per review (depends on code size)

---

## Option 2: Docker Container

**Best for:** Self-hosting, on-premise deployment, full control

### Advantages
- ✅ Complete control over infrastructure
- ✅ Can customize heavily
- ✅ Works with any Git platform
- ✅ One-time setup

### Disadvantages
- ❌ Users need to manage infrastructure
- ❌ Manual webhook configuration
- ❌ Requires maintenance

### Setup Instructions

1. **Create Production Dockerfile**:
   ```dockerfile
   # Dockerfile
   FROM python:3.11-slim
   
   # Install system dependencies
   RUN apt-get update && \
       apt-get install -y git && \
       rm -rf /var/lib/apt/lists/*
   
   WORKDIR /app
   
   # Copy and install requirements
   COPY backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application
   COPY backend/ .
   
   # Initialize RAG knowledge base
   RUN python init_rag.py
   
   # Expose port
   EXPOSE 5000
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=3s \
     CMD python -c "import requests; requests.get('http://localhost:5000/health')"
   
   # Run application
   CMD ["python", "run.py"]
   ```

2. **Create Docker Compose** (with MongoDB and Redis):
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   
   services:
     app:
       build: .
       ports:
         - "5000:5000"
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
         - GITHUB_TOKEN=${GITHUB_TOKEN}
         - MONGODB_URI=mongodb://mongodb:27017/pr_reviewer
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - mongodb
         - redis
       restart: unless-stopped
   
     mongodb:
       image: mongo:7
       volumes:
         - mongodb_data:/data/db
       restart: unless-stopped
   
     redis:
       image: redis:7-alpine
       restart: unless-stopped
   
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
       depends_on:
         - app
       restart: unless-stopped
   
   volumes:
     mongodb_data:
   ```

3. **Build and Push to Registry**:
   ```bash
   # Build
   docker build -t yourusername/pr-reviewer:latest .
   
   # Push to Docker Hub
   docker push yourusername/pr-reviewer:latest
   
   # Or push to GitHub Container Registry
   docker tag yourusername/pr-reviewer:latest ghcr.io/yourusername/pr-reviewer:latest
   docker push ghcr.io/yourusername/pr-reviewer:latest
   ```

4. **User Deployment**:
   ```bash
   # Users can run:
   docker run -d \
     -p 5000:5000 \
     -e OPENAI_API_KEY=sk-... \
     -e GITHUB_TOKEN=ghp_... \
     yourusername/pr-reviewer:latest
   
   # Or with docker-compose:
   wget https://raw.githubusercontent.com/yourusername/pr-reviewer/main/docker-compose.prod.yml
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Configure Webhook**:
   ```
   Webhook URL: http://your-server:5000/api/webhooks/github
   Content type: application/json
   Events: Pull requests
   Secret: [your-webhook-secret]
   ```

---

## Option 3: GitHub App

**Best for:** Enterprise, multi-tenant SaaS, professional distribution

### Advantages
- ✅ One-click installation for users
- ✅ Automatic webhook setup
- ✅ Fine-grained permissions
- ✅ Works across multiple repos/orgs
- ✅ Professional appearance

### Disadvantages
- ❌ More complex to set up
- ❌ Requires server infrastructure
- ❌ Need to handle multi-tenancy

### Setup Instructions

1. **Register GitHub App**:
   - Go to https://github.com/settings/apps/new
   - Fill in details:
     - **Name**: AI PR Reviewer
     - **Homepage URL**: https://your-domain.com
     - **Webhook URL**: https://your-domain.com/api/webhooks/github-app
     - **Webhook Secret**: Generate a secure secret
   
   - **Permissions**:
     - Repository permissions:
       - Contents: Read
       - Pull requests: Read & Write
       - Metadata: Read
     - Subscribe to events:
       - Pull request
       - Pull request review
   
   - Download private key (save as `github-app-key.pem`)

2. **Update Code for GitHub App Authentication**:
   
   Add to `backend/app/services/github_app_service.py`:
   ```python
   import jwt
   import time
   from typing import Optional
   
   class GitHubAppService:
       def __init__(self, app_id: str, private_key: str):
           self.app_id = app_id
           self.private_key = private_key
       
       def generate_jwt(self) -> str:
           """Generate JWT for GitHub App authentication"""
           now = int(time.time())
           payload = {
               'iat': now,
               'exp': now + 600,  # 10 minutes
               'iss': self.app_id
           }
           return jwt.encode(payload, self.private_key, algorithm='RS256')
       
       def get_installation_token(self, installation_id: str) -> str:
           """Get installation access token"""
           import requests
           
           jwt_token = self.generate_jwt()
           headers = {
               'Authorization': f'Bearer {jwt_token}',
               'Accept': 'application/vnd.github.v3+json'
           }
           
           url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
           response = requests.post(url, headers=headers)
           response.raise_for_status()
           
           return response.json()['token']
   ```

3. **Add Multi-Tenant Database Schema**:
   ```python
   # Store installation data
   installations = {
       'installation_id': str,
       'account_login': str,
       'account_type': str,  # 'User' or 'Organization'
       'repositories': [],
       'created_at': datetime,
       'settings': {
           'enabled': bool,
           'auto_review': bool
       }
   }
   ```

4. **Handle Installation Webhook**:
   ```python
   @api_bp.route("/webhooks/github-app", methods=["POST"])
   def github_app_webhook():
       event = request.headers.get("X-GitHub-Event")
       
       if event == "installation":
           # Store installation
           installation_id = request.json['installation']['id']
           # Save to database
       
       elif event == "pull_request":
           # Get installation token
           installation_id = request.json['installation']['id']
           token = github_app.get_installation_token(installation_id)
           
           # Process PR with installation-specific token
           # ...
   ```

5. **Deploy**:
   - Deploy to cloud (see Cloud Deployment Options below)
   - Update webhook URL in GitHub App settings
   - Publish app for users to install

6. **Users Install**:
   - Go to `https://github.com/apps/your-app-name`
   - Click "Install"
   - Select repositories
   - Done! Automatic webhook setup

### Cost Considerations
- Cloud hosting: $10-50/month (depends on usage)
- OpenAI API: Variable based on usage
- Optional: Charge users subscription fee

---

## Option 4: CLI Tool

**Best for:** Local development, manual reviews, CI integration

### Advantages
- ✅ No server needed
- ✅ Works offline (except LLM calls)
- ✅ Easy debugging
- ✅ Scriptable

### Disadvantages
- ❌ Manual trigger required
- ❌ No automatic PR comments
- ❌ Requires local setup

### Setup Instructions

1. **Create `setup.py`**:
   ```python
   from setuptools import setup, find_packages
   
   setup(
       name='pr-reviewer-cli',
       version='1.0.0',
       packages=find_packages(),
       include_package_data=True,
       install_requires=[
           'click>=8.0',
           'openai>=1.12.0',
           'langchain>=0.1.0',
           'PyGithub>=2.1.1',
           # ... other dependencies from requirements.txt
       ],
       entry_points={
           'console_scripts': [
               'pr-review=app.cli:main',
           ],
       },
       author='Your Name',
       description='AI-powered PR review tool',
       long_description=open('README.md').read(),
       long_description_content_type='text/markdown',
       url='https://github.com/yourusername/pr-reviewer-cli',
       classifiers=[
           'Development Status :: 4 - Beta',
           'Intended Audience :: Developers',
           'License :: OSI Approved :: MIT License',
           'Programming Language :: Python :: 3.11',
       ],
   )
   ```

2. **Create CLI Interface** (`backend/app/cli.py`):
   ```python
   import click
   import os
   from app.services.github_service import GitHubService
   from app.services.review_service import ReviewService
   
   @click.group()
   def main():
       """AI PR Reviewer CLI"""
       pass
   
   @main.command()
   @click.option('--repo', required=True, help='Repository (owner/name)')
   @click.option('--pr', required=True, type=int, help='PR number')
   @click.option('--openai-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
   @click.option('--github-token', envvar='GITHUB_TOKEN', help='GitHub token')
   @click.option('--post-comment', is_flag=True, help='Post review as comment')
   def review(repo, pr, openai_key, github_token, post_comment):
       """Review a pull request"""
       if not openai_key:
           raise click.ClickException('OPENAI_API_KEY required')
       
       os.environ['OPENAI_API_KEY'] = openai_key
       os.environ['GITHUB_TOKEN'] = github_token or ''
       
       click.echo(f'Reviewing PR #{pr} in {repo}...')
       
       github_service = GitHubService()
       review_service = ReviewService()
       
       owner, repo_name = repo.split('/')
       pr_data = github_service.get_pull_request(owner, repo_name, pr)
       diff_data = github_service.get_pr_diff(pr_data)
       result = review_service.analyze_code(diff_data)
       
       # Display results
       click.echo('\n=== Review Results ===')
       click.echo(f"Score: {result['overall_score']}/100")
       click.echo(f"Issues: {len(result['issues'])}")
       click.echo(f"\nSummary:\n{result['summary']}")
       
       if post_comment and github_token:
           github_service.post_review_comment(owner, repo_name, pr, result)
           click.echo('\n✅ Review posted as comment')
   
   @main.command()
   @click.option('--file', type=click.Path(exists=True), help='File to review')
   @click.option('--language', default='python', help='Programming language')
   def analyze(file, language):
       """Analyze a local file"""
       with open(file) as f:
           code = f.read()
       
       review_service = ReviewService()
       result = review_service.analyze_code_snippet(code, language)
       
       click.echo(f"\n=== Analysis Results ===")
       click.echo(f"Score: {result['overall_score']}/100")
       for issue in result['issues']:
           click.echo(f"[{issue['severity']}] {issue['message']}")
   
   if __name__ == '__main__':
       main()
   ```

3. **Package and Publish**:
   ```bash
   # Build package
   python setup.py sdist bdist_wheel
   
   # Upload to PyPI
   pip install twine
   twine upload dist/*
   ```

4. **Users Install**:
   ```bash
   pip install pr-reviewer-cli
   
   # Set credentials
   export OPENAI_API_KEY=sk-...
   export GITHUB_TOKEN=ghp_...
   
   # Review a PR
   pr-review review --repo owner/repo --pr 123
   
   # Analyze local file
   pr-review analyze --file mycode.py --language python
   ```

---

## Option 5: SaaS Platform

**Best for:** Commercial product, managed service, recurring revenue

### Advantages
- ✅ Centralized management
- ✅ User dashboard
- ✅ Subscription billing
- ✅ No user infrastructure needed
- ✅ Professional support

### Disadvantages
- ❌ Most complex to build
- ❌ Ongoing operational costs
- ❌ Need to handle scale
- ❌ Customer support burden

### Architecture Overview

```
┌─────────────┐
│   Web UI    │ (React dashboard)
└──────┬──────┘
       │
┌──────▼──────┐
│  API Server │ (Flask/FastAPI)
└──────┬──────┘
       │
┌──────▼──────┐
│  Database   │ (PostgreSQL + MongoDB)
│  - Users    │
│  - Repos    │
│  - Reviews  │
│  - Billing  │
└──────┬──────┘
       │
┌──────▼──────┐
│ Background  │ (Celery workers)
│  Workers    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Cache     │ (Redis)
└─────────────┘
```

### Key Components

1. **User Management**:
   - GitHub OAuth integration
   - Subscription tiers (Free/Pro/Enterprise)
   - API key management

2. **Repository Management**:
   - Connect GitHub repos
   - Configure review settings
   - View review history

3. **Billing System**:
   - Stripe integration
   - Usage tracking
   - Invoice generation

4. **Dashboard**:
   - Review analytics
   - Code quality trends
   - Team insights

5. **Admin Panel**:
   - User management
   - System monitoring
   - Usage statistics

### Tech Stack Recommendation
- **Frontend**: React + Next.js + TailwindCSS
- **Backend**: FastAPI (Python) or Node.js
- **Database**: PostgreSQL (users/billing) + MongoDB (reviews)
- **Cache**: Redis
- **Queue**: Celery or Bull
- **Auth**: Auth0 or Clerk
- **Payments**: Stripe
- **Hosting**: Vercel (frontend) + AWS/GCP (backend)

### Pricing Model Example
- **Free**: 10 reviews/month
- **Pro** ($29/month): 100 reviews/month
- **Team** ($99/month): 500 reviews/month
- **Enterprise**: Custom pricing

---

## Cloud Deployment Options

### AWS Deployment

**Using ECS (Elastic Container Service)**:
```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin [account].dkr.ecr.us-east-1.amazonaws.com
docker build -t pr-reviewer .
docker tag pr-reviewer:latest [account].dkr.ecr.us-east-1.amazonaws.com/pr-reviewer:latest
docker push [account].dkr.ecr.us-east-1.amazonaws.com/pr-reviewer:latest

# Deploy to ECS
aws ecs update-service --cluster pr-reviewer --service pr-reviewer-service --force-new-deployment
```

**Services Needed**:
- ECS or EKS for container orchestration
- RDS for PostgreSQL
- DocumentDB for MongoDB
- ElastiCache for Redis
- ALB for load balancing
- Route 53 for DNS
- Certificate Manager for SSL

**Monthly Cost**: ~$50-200 (depending on traffic)

### Google Cloud Platform

**Using Cloud Run** (serverless):
```bash
# Deploy to Cloud Run
gcloud builds submit --tag gcr.io/project-id/pr-reviewer
gcloud run deploy pr-reviewer \
  --image gcr.io/project-id/pr-reviewer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Monthly Cost**: ~$0-50 (pay per use)

### Heroku (Easiest)

```bash
# Deploy to Heroku
heroku create pr-reviewer-app
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
git push heroku main
```

**Monthly Cost**: ~$25-50 (Hobby/Pro tiers)

### Railway (Modern Alternative)

```bash
# Deploy to Railway
railway login
railway init
railway up
```

**Monthly Cost**: $5-20 (includes database)

### DigitalOcean App Platform

```bash
# Connect GitHub repo and auto-deploy
# Configure via web UI
```

**Monthly Cost**: $12-24 (includes database)

---

## Recommendation Matrix

| Use Case | Recommended Option | Complexity | Cost |
|----------|-------------------|------------|------|
| Quick prototype | GitHub Action | Low | Free |
| Personal projects | Docker + Railway | Low | $5-10/mo |
| Small team | Docker + DigitalOcean | Medium | $25-50/mo |
| Enterprise self-hosted | Docker + AWS | Medium | $50-200/mo |
| Public distribution | GitHub Action + Marketplace | Low | Free |
| Managed service | GitHub App + Cloud Run | High | $50-500/mo |
| Commercial SaaS | Custom platform + AWS | Very High | $200-2000/mo |

---

## Next Steps

1. **Choose your deployment strategy** based on target users
2. **Test locally** with Docker to ensure everything works
3. **Set up CI/CD** for automated deployments
4. **Monitor and iterate** based on user feedback
5. **Consider hybrid approach**: GitHub Action for easy onboarding + self-hosted for advanced users

For questions or support, open an issue on GitHub!
