# Quick Start - Kubernetes Deployment Commands

## 🚀 Deploy to Staging

```bash
# 1. Configure kubectl for EKS staging cluster
aws eks update-kubeconfig --name network-security-staging-cluster --region us-east-1

# 2. Create secrets from .env file
kubectl create secret generic network-security-secrets \
  --from-env-file=.env \
  -n network-security \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Deploy with Helm
helm upgrade --install network-security ./helm/network-security \
  --namespace network-security \
  --create-namespace \
  --values ./helm/network-security/values-staging.yaml \
  --set image.tag=latest

# 4. Verify deployment
kubectl get pods -n network-security -w

# 5. Test health endpoint
kubectl port-forward svc/network-security 8000:8000 -n network-security
curl http://localhost:8000/health
```

## 🎯 Deploy to Production

```bash
# 1. Configure kubectl for EKS production cluster
aws eks update-kubeconfig --name network-security-prod-cluster --region us-east-1

# 2. Deploy with Helm (Production)
helm upgrade --install network-security ./helm/network-security \
  --namespace network-security \
  --create-namespace \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.0.0 \
  --wait \
  --timeout 10m

# 3. Verify deployment
kubectl rollout status deployment/network-security -n network-security
kubectl get pods,svc,ingress -n network-security

# 4. Check health
curl https://api.network-security.example.com/health
```

## 🔄 Canary Deployment

```bash
# Deploy canary with 1 replica
helm install network-security-canary ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.1.0 \
  --set replicaCount=1 \
  --set autoscaling.enabled=false

# Monitor canary
kubectl logs -f deployment/network-security-canary -n network-security

# Promote if successful
helm upgrade network-security ./helm/network-security \
  --namespace network-security \
  --values ./helm/network-security/values-production.yaml \
  --set image.tag=v1.1.0

# Cleanup canary
helm uninstall network-security-canary -n network-security
```

## 🔙 Rollback

```bash
# Rollback using Helm
helm rollback network-security -n network-security

# Or rollback using kubectl
kubectl rollout undo deployment/network-security -n network-security
```

## 📊 Monitoring

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Deploy ServiceMonitor
kubectl apply -f k8s/servicemonitor.yaml

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login: admin / admin
```

## 🔧 Useful Commands

```bash
# View logs
kubectl logs -f deployment/network-security -n network-security --all-containers=true

# Execute into pod
kubectl exec -it deployment/network-security -n network-security -- /bin/bash

# Scale deployment
kubectl scale deployment network-security --replicas=10 -n network-security

# Update image
kubectl set image deployment/network-security \
  api=your-registry/network-security:v1.1.0 \
  -n network-security

# View resource usage
kubectl top pods -n network-security
kubectl top nodes

# View HPA status
kubectl get hpa -n network-security

# Trigger manual training job
kubectl create job --from=cronjob/model-training-job manual-training-$(date +%s) -n network-security
```

## 🔐 Secrets Management

```bash
# Create secrets from file
kubectl create secret generic network-security-secrets \
  --from-env-file=.env \
  -n network-security

# Or create secrets manually
kubectl create secret generic network-security-secrets \
  --from-literal=AWS_ACCESS_KEY_ID=your_key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your_secret \
  --from-literal=SLACK_WEBHOOK_URL=your_webhook \
  -n network-security

# View secrets (base64 encoded)
kubectl get secret network-security-secrets -n network-security -o yaml

# Decode secret
kubectl get secret network-security-secrets -n network-security -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d
```

## 🧪 Testing

```bash
# Test health endpoint
kubectl run test-curl --rm -i --restart=Never --image=curlimages/curl \
  -n network-security \
  -- curl -f http://network-security:8000/health

# Test prediction endpoint
kubectl run test-predict --rm -i --restart=Never --image=curlimages/curl \
  -n network-security \
  -- curl -X POST http://network-security:8000/predict \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_data.csv"

# Load testing
kubectl run load-test --rm -i --restart=Never --image=williamyeh/hey \
  -- -z 60s -c 10 http://network-security:8000/health
```

## 🗑️ Cleanup

```bash
# Delete all resources
helm uninstall network-security -n network-security

# Or using kubectl
kubectl delete namespace network-security

# Delete PVCs (if needed)
kubectl delete pvc -n network-security --all
```

## 📝 CI/CD Triggers

```bash
# Trigger CI workflow
git push origin main

# Create release tag (triggers CD to production)
git tag v1.0.0
git push origin v1.0.0

# Manual workflow dispatch
gh workflow run cd.yaml \
  --field deployment_strategy=rolling \
  --field environment=production
```

## 🔍 Troubleshooting

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n network-security

# Check deployment status
kubectl describe deployment network-security -n network-security

# Check HPA status
kubectl describe hpa network-security -n network-security

# Check ingress
kubectl describe ingress network-security -n network-security

# Check PVC binding
kubectl get pvc -n network-security
kubectl describe pvc <pvc-name> -n network-security

# View recent events
kubectl get events -n network-security --sort-by='.lastTimestamp'

# Check container logs (including init containers)
kubectl logs <pod-name> -n network-security --previous
kubectl logs <pod-name> -c init-container-name -n network-security
```

---

For detailed documentation, see [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)
