# 📦 Complete Deployment Guide — Django on AWS EKS

> **Infrastructure Strategy:** Cloud infrastructure (EKS cluster, IAM roles, add-ons) is provisioned **manually once**. All application deployments thereafter are handled **automatically via CI/CD pipeline** — this is the industry-standard GitOps approach and is absolutely production-ready.

---

## 🗺️ Deployment Roadmap

```
Phase 1: Provision EKS Cluster
        │
        ▼
Phase 2: Install EKS Add-ons
  ├── EBS CSI Driver
  ├── AWS Load Balancer Controller
  └── Cert Manager
        │
        ▼
Phase 3: Configure GitHub ↔ AWS Trust (OIDC)
        │
        ▼
Phase 4: Set GitHub Secrets
        │
        ▼
Phase 5: Push Code → CI/CD Auto-Deploys ♻️
```

---

## 🖥️ Prerequisites

Ensure the following tools are installed on your provisioning machine before starting:

| Tool | Purpose | Install |
|---|---|---|
| `aws-cli` | AWS API access | [docs.aws.amazon.com](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) |
| `eksctl` | EKS cluster management | [eksctl.io](https://eksctl.io/installation/) |
| `kubectl` | Kubernetes CLI | [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) |
| `helm` v3+ | Kubernetes package manager | [helm.sh](https://helm.sh/docs/intro/install/) |
| `docker` | Container build & push | [docker.com](https://docs.docker.com/get-docker/) |

Configure AWS CLI before proceeding:

```bash
aws configure
# AWS Access Key ID:     <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region name:   us-east-1
# Default output format: json
```

---

## Phase 1 — Create EKS Cluster

### 1.1 Create the Cluster

```bash
eksctl create cluster \
  --name django-cluster \
  --region us-east-1 \
  --nodegroup-name django-nodes \
  --node-type t3.small \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed
```

> ⏳ This takes ~15–20 minutes. The `--managed` flag uses AWS-managed node groups for automatic OS patching and lifecycle management.

### 1.2 Verify Cluster is Ready

```bash
kubectl get nodes
# All nodes should show STATUS = Ready
```

### 1.3 Enable IAM OIDC Provider

Required for IRSA (IAM Roles for Service Accounts) — allows Kubernetes pods to assume IAM roles securely without static credentials.

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster django-cluster \
  --region us-east-1 \
  --approve
```

---

## Phase 2 — Install EKS Add-ons

### 2.1 Amazon EBS CSI Driver

The EBS CSI driver enables Kubernetes PersistentVolumes backed by AWS EBS — required for stateful workloads like PostgreSQL.

**Step 1 — Create IAM Service Account (IRSA)**

```bash
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster django-cluster \
  --region us-east-1 \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve
```

**Step 2 — Install the EKS Add-on**

```bash
aws eks create-addon \
  --cluster-name django-cluster \
  --addon-name aws-ebs-csi-driver \
  --region us-east-1 \
  --service-account-role-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/AmazonEKS_EBS_CSI_DriverRole
```

**Step 3 — Verify Installation**

```bash
aws eks describe-addon \
  --cluster-name django-cluster \
  --region us-east-1 \
  --addon-name aws-ebs-csi-driver

kubectl get pods -n kube-system | grep ebs
# Expected: ebs-csi-controller pods in Running state
```

<details>
<summary>🔧 Troubleshooting — Conflict Error</summary>

If you see this error:
```
Conflicts found when trying to apply. Will not continue due to resolve conflicts mode.
Conflicts: ServiceAccount ebs-csi-controller-sa - .metadata.labels.app.kubernetes.io/managed-by
```

Clean up and reinstall:
```bash
kubectl delete deployment ebs-csi-controller -n kube-system
kubectl delete daemonset ebs-csi-node -n kube-system
kubectl delete sa ebs-csi-controller-sa -n kube-system

# Then re-run the create-addon command with OVERWRITE flag:
aws eks create-addon \
  --cluster-name django-cluster \
  --addon-name aws-ebs-csi-driver \
  --region us-east-1 \
  --service-account-role-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/AmazonEKS_EBS_CSI_DriverRole \
  --resolve-conflicts OVERWRITE
```
</details>

---

### 2.2 AWS Load Balancer Controller

Provisions AWS Application Load Balancers (ALB) automatically from Kubernetes Ingress resources.

**Step 1 — Create IAM Policy**

```bash
# Download the policy document
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json

# Create the policy in AWS
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json
```

**Step 2 — Apply CRDs**

```bash
kubectl apply -k "github.com/kubernetes-sigs/aws-load-balancer-controller//config/default?ref=v2.12.0"
```

**Step 3 — Add Helm Repo**

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update
```

**Step 4 — Create IAM Service Account**

```bash
eksctl create iamserviceaccount \
  --cluster django-cluster \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region us-east-1
```

**Step 5 — Get VPC ID and Install Controller**

```bash
# Get your cluster VPC ID
VPC_ID=$(aws eks describe-cluster \
  --name django-cluster \
  --region us-east-1 \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text)

echo "VPC ID: $VPC_ID"

# Install via Helm
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=django-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=us-east-1 \
  --set vpcId=$VPC_ID
```

**Step 6 — Verify**

```bash
kubectl get deployment -n kube-system aws-load-balancer-controller
# Expected: AVAILABLE = 2/2
```

---

### 2.3 Cert Manager

Automates TLS certificate provisioning and renewal via Let's Encrypt.

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true
```

**Verify Installation**

```bash
kubectl get pods -n cert-manager
# Expected: cert-manager, cert-manager-cainjector, cert-manager-webhook pods Running

kubectl get crds | grep cert-manager
# Should list certificate-related CRDs
```

---

## Phase 3 — Configure GitHub ↔ AWS Trust (OIDC)

This is the **secure, keyless authentication** approach. GitHub Actions assumes an IAM role directly — no long-lived AWS access keys stored as secrets.

> 📖 Reference: [GitHub OIDC with AWS Documentation](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)

### 3.1 Register GitHub as an Identity Provider in AWS

1. Go to **AWS Console → IAM → Identity Providers**
2. Click **Add Provider**
3. Select **OpenID Connect**
4. Fill in:
   - **Provider URL:** `https://token.actions.githubusercontent.com`
   - **Audience:** `sts.amazonaws.com`
5. Click **Add Provider**

### 3.2 Create IAM Role for GitHub Actions

1. Go to **IAM → Roles → Create Role**
2. Select **Web Identity** as trusted entity type
3. Configure:
   - **Identity Provider:** `token.actions.githubusercontent.com`
   - **Audience:** `sts.amazonaws.com`
   - **GitHub organization:** `<your-github-username>`
   - **GitHub repository:** `sai-prj2`
   - **GitHub branch:** `main`
4. Attach permission: **`AmazonEC2ContainerRegistryFullAccess`**
5. Name the role: **`Github`**
6. Create the role

### 3.3 Add Inline Policy for EKS Access

Attach this inline policy to the `Github` IAM role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSAccess",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "arn:aws:eks:us-east-1:<YOUR-AWS-ACCOUNT-ID>:cluster/django-cluster"
    }
  ]
}
```

> 💡 This grants only the minimum EKS permissions needed. ECR full access is handled by the managed policy attached above.

### 3.4 Grant EKS Cluster Access to the IAM Role

Using the modern **EKS Access Entries** approach (EKS v1.28+):

```bash
# Step 1 — Create access entry
aws eks create-access-entry \
  --cluster-name django-cluster \
  --principal-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/Github \
  --type STANDARD \
  --region us-east-1

# Step 2 — Associate cluster admin policy
aws eks associate-access-policy \
  --cluster-name django-cluster \
  --principal-arn arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/Github \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --region us-east-1
```

> 🔐 **Least Privilege Tip:** Replace `AmazonEKSClusterAdminPolicy` with `AmazonEKSEditPolicy` in production to restrict GitHub Actions from making destructive cluster changes.

<details>
<summary>🔧 Alternative — Legacy aws-auth ConfigMap method (EKS < v1.28)</summary>

```bash
kubectl edit configmap aws-auth -n kube-system
```

Add under `mapRoles`:
```yaml
- rolearn: arn:aws:iam::<YOUR-AWS-ACCOUNT-ID>:role/Github
  username: github-actions
  groups:
    - system:masters
```
</details>

---

## Phase 4 — Configure GitHub Repository Secrets

Go to your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Description |
|---|---|---|
| `AWS_ROLE_ARN` | `arn:aws:iam::<account-id>:role/Github` | IAM role for OIDC auth |
| `AWS_REGION` | `us-east-1` | AWS region |
| `ECR_REPOSITORY` | `saiapp` | ECR repository name |
| `EKS_CLUSTER_NAME` | `django-cluster` | EKS cluster name |
| `DJANGO_SECRET_KEY` | `<your-secret-key>` | Django app secret |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain.com` | Allowed CSRF origins |
| `DJANGO_SUPERUSER_PASSWORD` | `<admin-password>` | Django admin password |
| `POSTGRES_PASSWORD` | `<db-password>` | PostgreSQL password |

> ⚠️ **Never** commit these values to the repository. GitHub Actions injects them as environment variables at runtime.

---

## Phase 5 — CI/CD Pipeline (Auto-Deploy on Push)

Once Phases 1–4 are complete, every push to `main` triggers the GitHub Actions workflow automatically.

### What the Pipeline Does

```
git push origin main
        │
        ▼
[GitHub Actions Triggered]
        │
        ├── 1. Checkout code
        ├── 2. Configure AWS credentials via OIDC (no static keys!)
        ├── 3. Login to Amazon ECR
        ├── 4. Docker build → tag with Git SHA → push to ECR
        ├── 5. Update kubeconfig for EKS
        └── 6. helm upgrade --install django-app ./django-chart
                  --set image.tag=${{ github.sha }}
```

### Manual Deploy (if needed)

```bash
# Authenticate
aws eks update-kubeconfig --name django-cluster --region us-east-1

# Deploy / Upgrade
helm upgrade --install django-app ./django-chart \
  --set image.repository=<your-ecr-uri>/saiapp \
  --set image.tag=<git-sha-or-tag> \
  --namespace production \
  --create-namespace \
  --wait

# Verify rollout
kubectl get pods -n production
kubectl get svc -n production
```

### Rollback

```bash
# View release history
helm history django-app -n production

# Rollback to previous version
helm rollback django-app <REVISION-NUMBER> -n production

# Or rollback to last known good release
helm rollback django-app -n production
```

---

## 🔍 Verification Checklist

After a successful deployment, verify each layer:

```bash
# ✅ Cluster nodes are healthy
kubectl get nodes

# ✅ Application pods are running
kubectl get pods -n production

# ✅ Service and ingress are configured
kubectl get svc,ingress -n production

# ✅ Load balancer was provisioned
kubectl describe ingress -n production

# ✅ TLS certificate issued
kubectl get certificate -n production

# ✅ Check application logs
kubectl logs -l app=django-app -n production --tail=50

# ✅ EBS CSI running
kubectl get pods -n kube-system | grep ebs

# ✅ Load Balancer Controller running
kubectl get deployment -n kube-system aws-load-balancer-controller

# ✅ Cert Manager running
kubectl get pods -n cert-manager
```

---

## ❓ Infrastructure Strategy — Manual vs Full Automation

> **"Is it good to create cloud infra manually and let CI/CD handle the rest?"**

**Yes — this is the recommended approach**, and here's why:

| Concern | Manual Infra (Terraform/eksctl) | Full CI/CD |
|---|---|---|
| **Cluster creation** | ✅ Provision once, rarely changes | ❌ Risky to auto-destroy/recreate |
| **Add-ons (EBS, ALB, Cert)** | ✅ Configured once, stable | ❌ Unnecessarily re-run on every deploy |
| **Application deployments** | ❌ Error-prone, slow | ✅ Automated, consistent, auditable |
| **Config changes** | ✅ Reviewed via PR before applying | ✅ Also good via GitOps (ArgoCD/Flux) |

**Best Practice Pattern:**
- **Infrastructure** → Provision with `eksctl` / Terraform (one-time or via separate IaC pipeline)
- **Application** → Deploy and update via GitHub Actions CI/CD on every `git push`

This is exactly how this project is architected.

---

## 📌 Quick Reference — Key Commands

```bash
# Cluster
eksctl get cluster --region us-east-1

# Nodes
kubectl get nodes -o wide

# All resources in production namespace
kubectl get all -n production

# Helm releases
helm list -A

# Describe a failing pod
kubectl describe pod <pod-name> -n production

# Get pod logs
kubectl logs <pod-name> -n production

# Exec into a running container
kubectl exec -it <pod-name> -n production -- /bin/bash
```

---

<div align="center">

*For application-level documentation, refer to [README.md](./README.md)*

</div>