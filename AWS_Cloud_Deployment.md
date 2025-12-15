### 2. `DEPLOYMENT.md`

This file answers the "Extra Credit" question. It explains the cloud architecture in simple, logical terms.

```markdown
# AWS Cloud Deployment Strategy

This document outlines how I would deploy this application to a production environment on AWS. The architecture focuses on cost-efficiency (using serverless where possible) and reliability.

## Architecture Overview



The system consists of three main components:

1.  **Database:** Amazon RDS (PostgreSQL)
2.  **Ingestion Pipeline:** AWS Fargate (Scheduled Containers)
3.  **REST API:** AWS Lambda & API Gateway

---

## Component Details

### 1. Database: Amazon RDS (PostgreSQL)
I would migrate from the local SQLite database to **Amazon RDS running PostgreSQL**.

* **Why?** SQLite is excellent for development but cannot handle high concurrency in production. PostgreSQL on RDS gives us automated backups, easy scaling, and the ability to handle millions of weather records without performance degradation.

### 2. Data Ingestion: AWS Fargate
I would deploy the `scripts/ingest.py` script as a Docker container running on **AWS Fargate**.

* **Why Fargate?** While AWS Lambda is cheaper, it has a hard 15-minute timeout limit. Ingesting 20+ years of historical data might take longer than 15 minutes. Fargate allows the script to run as long as needed until the job is done.
* **Scheduling:** I would use **Amazon EventBridge** to trigger this Fargate task automatically once every 24 hours (e.g., at 2:00 AM) to ensure our data is always up to date.

### 3. API Layer: AWS Lambda + API Gateway
I would deploy the FastAPI application (`app.py`) using **AWS Lambda** fronted by **Amazon API Gateway**.

* **Why Lambda?** The API traffic will likely be variable. Lambda is "Serverless," meaning we only pay when a user actually makes a request. If nobody queries the API at night, it costs us $0. This is much cheaper than paying for a server (EC2) to sit idle 24/7.
* **Why API Gateway?** It acts as a secure "front door" for the API, handling routing, security (API Keys), and traffic throttling to protect our backend.

---

## Automation (DevOps)

To ensure the system is maintainable and robust, I would use the following tools:

### Infrastructure as Code (Terraform)
I would use **Terraform** to define all our AWS resources (Database, Lambda, Fargate) in code. This ensures that our infrastructure is reproducible. We can spin up a duplicate "Staging" environment to test changes safely before pushing to "Production."

### CI/CD Pipeline (GitHub Actions)
I would set up a **GitHub Actions** pipeline to automate deployment:
1.  **Test:** Every time code is pushed to GitHub, it automatically runs `pytest` to catch bugs.
2.  **Build:** If tests pass, it builds a Docker image for the ingestion script and pushes it to Amazon ECR.
3.  **Deploy:** It automatically updates the Lambda function with the new API code.