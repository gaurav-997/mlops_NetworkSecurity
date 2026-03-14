# Kubernetes Deployment Guide - Network Security MLOps

This guide covers deploying the Network Security MLOps application on Kubernetes using both raw manifests and Helm charts.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Deployment Options](#deployment-options)
4. [Configuration](#configuration)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)
7. [Production Checklist](#production-checklist)

---

## Prerequisites

### Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install AWS CLI (for EKS)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Kubernetes Cluster
- **AWS EKS**: Managed Kubernetes service (recommended)
- **GKE**: Google Kubernetes Engine
- **AKS**: Azure Kubernetes Service
- **Self-hosted**: kubeadm, k3s, or kind for development

### AWS EKS Cluster Setup
```bash
# Create EKS cluster
eksctl create cluster \
  --name network-security-prod \
  --region us-east-1 \
  --nodegroup-name ml-nodes \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed

# Configure kubectl
aws eks update-kubeconfig --name network-security-prod --region us-east-1
```

---

## Quick Start

### Option 1: Deploy with Helm (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/your-org/network-security.git
cd network-security

# 2. Create namespace
kubectl create namespace network-security

# 3. Create secrets (from .env file)
kubectl create secret generic network-security-secrets \
  --from-env-file=.env \
  -n network-security

# 4. Install with Helm (Staging)
helm install network-security ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-staging.yaml \
  --set image.tag=latest

# 5. Verify deployment
kubectl get pods -n network-security
kubectl get services -n network-security

# 6. Check health
kubectl port-forward svc/network-security 8000:8000 -n network-security
curl http://localhost:8000/health
```

### Option 2: Deploy with Kustomize

```bash
# 1. Update image tag in kustomization.yaml
cd k8s
kubectl apply -k .

# 2. Verify
kubectl get all -n network-security
```

### Option 3: Deploy with Raw Manifests

```bash
# Apply manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/cronjob.yaml
```

---

## Deployment Options

### Production Deployment

```bash
helm upgrade --install network-security ./helm/network-security \
  --namespace network-security \
  --create-namespace \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.0.0 \
  --set secrets.AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  --set secrets.AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  --wait \
  --timeout 10m
```

### Canary Deployment

```bash
# Deploy canary with 10% traffic
helm install network-security-canary ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.1.0 \
  --set replicaCount=1 \
  --set autoscaling.enabled=false \
  --set service.name=network-security-canary

# Monitor canary metrics
kubectl logs -f deployment/network-security-canary -n network-security

# Promote canary if successful
helm upgrade network-security ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.1.0

# Rollback if needed
helm rollback network-security -n network-security
```

### Blue-Green Deployment

```bash
# Deploy green environment
helm install network-security-green ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.1.0 \
  --set service.name=network-security-green

# Test green environment
kubectl run test-client --rm -i --restart=Never --image=curlimages/curl \
  -n network-security \
  -- curl -f http://network-security-green:8000/health

# Switch traffic (update ingress)
kubectl patch ingress network-security -n network-security --type merge \
  -p '{"spec":{"rules":[{"host":"api.example.com","http":{"paths":[{"path":"/","backend":{"service":{"name":"network-security-green","port":{"number":8000}}}}]}}]}}'

# Remove blue after validation
helm uninstall network-security -n network-security
helm install network-security ./helm/network-security-green
```

---

## Configuration

### Environment Variables

Edit `k8s/configmap.yaml` or use Helm values:

```yaml
env:
  APP_ENV: production
  AWS_REGION: us-east-1
  MODEL_BUCKET: your-model-bucket
  MLFLOW_TRACKING_URI: http://mlflow:5000
  LOG_LEVEL: INFO
```

### Secrets Management

**Option 1: Kubernetes Secrets (Basic)**
```bash
kubectl create secret generic network-security-secrets \
  --from-literal=AWS_ACCESS_KEY_ID=your_key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your_secret \
  -n network-security
```

**Option 2: External Secrets Operator (Recommended)**
```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Create SecretStore (AWS Secrets Manager)
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: network-security
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: network-security-sa
EOF

# Create ExternalSecret
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: network-security-secrets
  namespace: network-security
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: network-security-secrets
  data:
    - secretKey: AWS_ACCESS_KEY_ID
      remoteRef:
        key: network-security/credentials
        property: aws_access_key_id
    - secretKey: AWS_SECRET_ACCESS_KEY
      remoteRef:
        key: network-security/credentials
        property: aws_secret_access_key
EOF
```

### IAM Roles for Service Accounts (IRSA)

```bash
# Create IAM role for pod
eksctl create iamserviceaccount \
  --name network-security-sa \
  --namespace network-security \
  --cluster network-security-prod \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve \
  --override-existing-serviceaccounts
```

### Storage Configuration

**AWS EFS for Shared Storage:**
```bash
# Install EFS CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.5"

# Create EFS filesystem (via AWS Console or CLI)
aws efs create-file-system --region us-east-1 --tags Key=Name,Value=network-security-efs

# Update PVC with your EFS ID in k8s/pvc.yaml
```

---

## Monitoring Setup

### Install Prometheus Operator

```bash
# Add Prometheus helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin
```

### Deploy ServiceMonitor

```bash
# ServiceMonitor will auto-discover /metrics endpoint
kubectl apply -f k8s/servicemonitor.yaml

# Access Prometheus UI
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login: admin / admin
```

### Import Grafana Dashboard

1. Access Grafana at http://localhost:3000
2. Go to Dashboards → Import
3. Upload `grafana/dashboards/model_monitoring.json`
4. Select Prometheus data source

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n network-security

# Describe pod
kubectl describe pod <pod-name> -n network-security

# Check logs
kubectl logs <pod-name> -n network-security

# Common issues:
# - Image pull errors: Check image registry credentials
# - Pending state: Check PVC binding and node resources
# - CrashLoopBackOff: Check application logs and health probes
```

### Health Check Failures

```bash
# Test health endpoint directly
kubectl exec -it <pod-name> -n network-security -- curl localhost:8000/health

# Check probe configuration
kubectl describe pod <pod-name> -n network-security | grep -A 10 "Liveness\|Readiness"

# Adjust probe timing if needed (increase initialDelaySeconds)
```

### PVC NotBound

```bash
# Check PVC status
kubectl get pvc -n network-security

# Describe PVC
kubectl describe pvc <pvc-name> -n network-security

# Check StorageClass
kubectl get storageclass

# For EFS issues:
kubectl logs -n kube-system -l app=efs-csi-controller
```

### Ingress Not Working

```bash
# Check ingress resource
kubectl get ingress -n network-security
kubectl describe ingress network-security -n network-security

# Check AWS Load Balancer Controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verify DNS
nslookup api.network-security.example.com
```

### HPA Not Scaling

```bash
# Check HPA status
kubectl get hpa -n network-security
kubectl describe hpa network-security -n network-security

# Check metrics server
kubectl top nodes
kubectl top pods -n network-security

# Install metrics-server if missing
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Production Checklist

### Security
- [ ] Use IRSA instead of access keys
- [ ] Enable pod security standards
- [ ] Configure network policies
- [ ] Use External Secrets Operator
- [ ] Enable encryption at rest
- [ ] Configure RBAC properly
- [ ] Use private container registry
- [ ] Enable audit logging

### High Availability
- [ ] Deploy across multiple AZs
- [ ] Configure pod anti-affinity
- [ ] Set appropriate replica counts (min 3)
- [ ] Configure HPA with proper metrics
- [ ] Use PodDisruptionBudgets
- [ ] Configure topology spread constraints

### Monitoring & Alerting
- [ ] Deploy Prometheus & Grafana
- [ ] Configure ServiceMonitor
- [ ] Set up alerting rules
- [ ] Configure Slack/PagerDuty notifications
- [ ] Enable distributed tracing
- [ ] Set up log aggregation

### Performance
- [ ] Configure resource requests/limits
- [ ] Use appropriate instance types
- [ ] Enable cluster autoscaler
- [ ] Configure caching (Redis)
- [ ] Use CDN for static assets
- [ ] Enable HTTP/2 on ingress

### Backup & Disaster Recovery
- [ ] Configure automated backups (Velero)
- [ ] Test restore procedures
- [ ] Document recovery steps
- [ ] Set up multi-region if needed
- [ ] Backup model artifacts to S3

### CI/CD Integration
- [ ] Set up GitHub Actions workflows
- [ ] Configure automated testing
- [ ] Implement deployment strategies
- [ ] Set up automated rollbacks
- [ ] Configure deployment notifications

---

## Useful Commands

```bash
# Get all resources
kubectl get all -n network-security

# Watch pod status
kubectl get pods -n network-security -w

# Stream logs
kubectl logs -f deployment/network-security -n network-security

# Execute commands in pod
kubectl exec -it <pod-name> -n network-security -- /bin/bash

# Port forward
kubectl port-forward svc/network-security 8000:8000 -n network-security

# Restart deployment
kubectl rollout restart deployment/network-security -n network-security

# Scale manually
kubectl scale deployment network-security --replicas=5 -n network-security

# Update image
kubectl set image deployment/network-security api=your-registry/network-security:v1.1.0 -n network-security

# Rollback
kubectl rollout undo deployment/network-security -n network-security

# Check rollout history
kubectl rollout history deployment/network-security -n network-security

# Delete resources
kubectl delete -f k8s/
helm uninstall network-security -n network-security
```

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [External Secrets Operator](https://external-secrets.io/)

For issues and questions, contact: your-team@example.com
