# Dockerization

- Multi-stage Dockerfile
- Separate containers:
  - backend
  - frontend
  - postgres
  - redis
  - celery

# CI/CD

- GitHub Actions:
  - Run tests
  - Lint code
  - Build Docker image

# Deployment

- Production environment variables
- Database migrations
- HTTPS enabled
- NGINX reverse proxy

# Docker

Multi-stage build:

- base
- test
- production

# ECS Configuration

- Task Definition JSON
- CPU/Memory limits
- Environment variables
- IAM roles

# CI/CD

GitHub Actions:

1. Run tests
2. Lint
3. Build Docker image
4. Push to ECR
5. Trigger ECS deployment

# Infrastructure as Code

All AWS resources must be provisioned using Terraform.

No manual AWS console setup allowed.

# Terraform Requirements

- Use variables for environment configs
- Support dev and prod workspaces
- Output ALB URL
- Secure RDS access via security groups
- Store Terraform state remotely (S3 + DynamoDB locking)

# ECS Deployment Flow

CI Pipeline:

1. Build Docker image
2. Push to ECR
3. Update ECS task definition
4. Trigger service rollout
