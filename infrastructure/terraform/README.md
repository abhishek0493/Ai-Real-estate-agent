# Infrastructure as Code

This project provisions:

- VPC
- Public + Private Subnets
- Application Load Balancer
- ECS Fargate Service
- RDS PostgreSQL
- ElastiCache Redis
- ECR Repository
- IAM Roles

# Principles

- Stateless containers
- Private RDS subnet
- Security groups restricted by layer
- Environment variable injection via ECS task definition
- No hardcoded secrets
