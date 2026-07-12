# AWS EC2 Deployment — Internal Employee Assistant

## Deployment Target

This deployment runs the full-stack app on one EC2 instance using Docker Compose.

Services:

- PostgreSQL
- Qdrant
- Ollama
- FastAPI backend
- Nginx frontend

## Required EC2 Security Group Ports

Open inbound ports:

- `22` for SSH
- `80` for frontend
- `8000` for backend API

Optional for debugging only:

- `5432` PostgreSQL
- `6333` Qdrant
- `11434` Ollama

For production, keep database/vector/LLM ports private.

## Required Local Files on EC2

Create these real env files on EC2:

```text
backend/.env.production
infra/aws-ec2/.env.ec2