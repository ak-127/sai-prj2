# 🚀 Django on AWS EKS — Production-Ready Kubernetes Deployment Pipeline

<div align="center">

![AWS EKS](https://img.shields.io/badge/AWS_EKS-Kubernetes-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Django](https://img.shields.io/badge/Django-Web_App-092E20?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-Package_Manager-0F1689?style=for-the-badge&logo=helm&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**A fully automated, production-grade CI/CD pipeline that builds, containerizes, and deploys a Django application to AWS EKS using Helm — with zero-downtime releases, automated rollbacks, and environment-specific configurations.**

</div>

---

## 📌 Project Overview

This project demonstrates end-to-end DevOps engineering by designing and implementing a complete deployment pipeline for a Django web application. The pipeline follows industry best practices for scalability, security, and reliability — simulating a real-world production workflow.

> **Goal:** Eliminate manual deployments. Every `git push` to `main` triggers a fully automated pipeline that tests, builds, publishes, and deploys the application to a managed Kubernetes cluster on AWS.

---

## 🏗️ Architecture

```
Developer Push (GitHub)
        │
        ▼
┌───────────────────┐
│  GitHub Actions   │  ◄── CI/CD Pipeline Trigger
│  (CI/CD Workflow) │
└────────┬──────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
 Build &    Run Tests
 Lint       (Django)
    │
    ▼
┌──────────────────┐
│  Docker Build &  │
│  Push to ECR /   │
│  Docker Hub      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Helm Deploy    │  ◄── Upgrade / Rollback
│  (django-chart)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    AWS EKS       │  ◄── Managed Kubernetes
│   (Production)   │
└──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Application** | Python / Django | Web framework |
| **Containerization** | Docker | Build reproducible images |
| **Orchestration** | Kubernetes (AWS EKS) | Deploy, scale, self-heal |
| **Package Management** | Helm | Templated K8s manifests |
| **CI/CD** | GitHub Actions | Automated pipeline |
| **Cloud** | AWS (EKS, ECR, IAM) | Managed infrastructure |
| **Scripting** | Bash | Automation utilities |

---

## ✨ Key DevOps Features

- **Fully Automated CI/CD** — Code merged to `main` deploys to production without manual intervention
- **Containerized Workload** — Multi-stage Dockerfile with optimized image layers and `.dockerignore`
- **Helm Chart Packaging** — Reusable, configurable K8s deployment via `django-chart/`
- **Zero-Downtime Deploys** — Rolling update strategy configured in Helm values
- **Automated Rollbacks** — Helm's revision history enables instant rollback on failure
- **Entrypoint Automation** — `entrypoint.sh` handles DB migrations and static file collection at startup

- **Environment Separation** — Config management for dev/prod via Helm values overrides
- **Security Best Practices** — Secrets managed via GitHub Actions secrets, not hardcoded

---

## 📁 Repository Structure

```
sai-prj2/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD pipeline definitions
├── blog/                   # Django app — Blog module
├── core/                   # Django app — Core logic
├── saikrupax/              # Django project settings & URL routing
├── django-chart/           # Helm chart for Kubernetes deployment
│   ├── templates/          # K8s manifests (Deployment, Service, Ingress, etc.)
│   └── values.yaml         # Default Helm values (image, replicas, resources)
├── scripts/                # Utility shell scripts (cluster setup, helpers)
├── static/                 # Static assets (CSS, JS)
├── templates/              # Django HTML templates
├── Dockerfile              # Container image definition
├── entrypoint.sh           # Container startup script (migrations, collectstatic)
├── requirements.txt        # Python dependencies
└── manage.py               # Django management entry point
```

---

## ⚙️ CI/CD Pipeline — How It Works

The GitHub Actions workflow is triggered on every push to the `main` branch:

**Stage 1 — Build & Test**
```
Checkout Code → Install Dependencies → Run Django Tests → Lint
```

**Stage 2 — Containerize**
```
Docker Build → Tag Image with Git SHA → Push to Container Registry
```

**Stage 3 — Deploy to EKS**
```
Configure AWS Credentials → Update kubeconfig → Helm Upgrade --install
```

If the Helm deploy fails, the pipeline exits non-zero and the previous Helm revision remains live — ensuring the application never goes down due to a broken deploy.

---

## 🚀 Getting Started

### Prerequisites

- AWS CLI configured with appropriate IAM permissions
- `kubectl` installed and configured
- `helm` v3+
- Docker

### 1. Clone the Repository

```bash
git clone https://github.com/ak-127/sai-prj2.git
cd sai-prj2
```

### 2. Run Locally with Docker

```bash
# Build the image
docker build -t sai-prj2:local .

# Run the container
docker run -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DEBUG=True \
  sai-prj2:local
```

App will be available at `http://localhost:8000`

### 3. Deploy to Kubernetes with Helm

```bash
# Authenticate with your EKS cluster
aws eks update-kubeconfig --name <your-cluster-name> --region <aws-region>

# Install / Upgrade the Helm release
helm upgrade --install django-app ./django-chart \
  --set image.tag=<your-image-tag> \
  --set image.repository=<your-ecr-or-dockerhub-repo> \
  --namespace production \
  --create-namespace
```

### 4. Rollback if Needed

```bash
# View release history
helm history django-app

# Rollback to previous version
helm rollback django-app <revision-number>
```

---

## 🔐 GitHub Actions Secrets Required

Configure these secrets in your GitHub repository (`Settings → Secrets and variables → Actions`):

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | Target AWS region |
| `EKS_CLUSTER_NAME` | EKS cluster name |
| `DOCKER_REGISTRY` | Container registry URL |
| `DJANGO_SECRET_KEY` | Django secret key for production |

---

## 📊 Infrastructure Highlights

- **AWS EKS** — Managed Kubernetes control plane; worker nodes auto-scaled via node groups
- **Helm** — All Kubernetes manifests (Deployment, Service, ConfigMap, HPA) are templated and version-controlled
- **Rolling Updates** — New pods are created before old ones are terminated, ensuring zero downtime
- **Resource Limits** — CPU and memory requests/limits defined in Helm values to prevent noisy-neighbor issues
- **Health Checks** — Liveness and readiness probes configured to ensure traffic only reaches healthy pods

---


## 📈 What This Project Demonstrates

| DevOps Skill | Implementation |
|---|---|
| CI/CD Pipeline Design | GitHub Actions multi-stage workflow |
| Containerization | Optimized Dockerfile with entrypoint scripting |
| Kubernetes | EKS cluster, Deployments, Services, Health Probes |
| Helm Packaging | Custom chart with parameterized values |
| Cloud (AWS) | EKS, ECR, IAM roles & permissions |
| Automation | Shell scripts for cluster operations |
| Release Management | Semantic versioning with 20+ tags |
| Security | Secrets management, no credentials in code |

---

📖 **Full deployment setup:** See [DEPLOYMENT.md](./DEPLOYMENT.md)

---

<div align="center">

*Built with a focus on automation, reliability, and production-grade DevOps practices.*

</div>