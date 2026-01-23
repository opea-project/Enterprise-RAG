# Amazon EKS Deployment Guide

This guide provides step-by-step instructions for deploying the Intel® AI for Enterprise RAG solution on Amazon Elastic Kubernetes Service (EKS).

## Table of Contents

- [Prerequisites](#prerequisites)
- [AWS Configuration](#aws-configuration)
- [EKS Cluster Access](#eks-cluster-access)
- [ECR Registry Setup (Optional)](#ecr-registry-setup-optional)
- [Service Account and RBAC Configuration](#service-account-and-rbac-configuration)
- [Storage Configuration](#storage-configuration)
- [Pipeline Configuration (Optional)](#pipeline-configuration-optional)
- [Application Configuration](#application-configuration)
- [Deployment](#deployment)

## Prerequisites

Before deploying to EKS, ensure you have:

- AWS CLI installed and configured
- [Terraform installed](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli#install-terraform)
- `kubectl` installed
- Access to an existing EKS cluster or permissions to create one. See below for Terraform deployment instructions.
- Appropriate AWS IAM permissions for EKS
- Appropriate AWS IAM permissions for ECR (Optional)

## AWS Configuration

Configure your AWS credentials:

```bash
aws configure
```

You will be prompted to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

## Manual EKS Deployment

Follow AWS instructions to create an EKS cluster manually if you prefer not to use Terraform automated deployment.

## Installation on an existing EKS cluster

You can deploy the Intel® AI for Enterprise RAG solution on an existing EKS cluster, including one that may have been created during the installation of [Nutanix Enterprise AI](nutanix/NUTANIX-AI-EKS.md) on AWS EKS. In that case, skip the cluster setup and proceed to [EKS Cluster Access](#eks-cluster-access).

## EKS Terraform Automated Deployment

### Clone the Repository

```bash
git clone https://github.com/opea-project/Enterprise-RAG.git
cd Enterprise-RAG/deployment/terraform/aws/nutanix/eks-erag
```

### Configure Deployment Settings

Modify the `locals` block in `Enterprise-RAG/deployment/terraform/aws/nutanix/eks-erag/main.tf`:

```hcl
locals {
  name   = "your-cluster-name"    # Update with your desired name
  region = "us-east-1"           # Update with your preferred region
  tags = {
    Owner    = "your@email.com"
    Project  = "Intel AI for Enterprise RAG"
    Duration = "0"              
  }
}
```

### Deploy Infrastructure

Run the following Terraform commands:

```bash
terraform init
terraform plan
terraform apply
```


## EKS Cluster Access

### Grant User Access

Ensure your IAM user or role has been granted access to the EKS cluster:

1. Add the user/role to the cluster's IAM access entries
2. Configure EKS cluster endpoint access:
   - Add your development machine's public IP to the cluster's networking endpoint allowlist (if using private endpoint)
   - Or ensure the cluster has public endpoint access enabled

### Configure kubectl for EKS Cluster

```bash
# Verify AWS identity
aws sts get-caller-identity

# Configure kubectl for your EKS cluster
aws eks update-kubeconfig --region us-east-1 --name $(terraform output -raw cluster_name)

# Test the connection
kubectl get svc

# Verify Nodes
kubectl get nodes
```

## ECR Registry Setup (Optional)
> [!IMPORTANT] 
> This step is only needed if you don't have access to docker.io or your images are not in release version

### Create ECR Repositories

Create ECR repositories for your container images (if not already created):

```bash
aws ecr create-repository --repository-name <repository-name> --region <your-region>
```

### Login to ECR

Authenticate Docker to your ECR registry:

```bash
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<your-region>.amazonaws.com
```

### Push Images

Update and push images to ECR using the provided script:

```bash
cd deployment
./update_images.sh -- --registry <account-id>.dkr.ecr.<your-region>.amazonaws.com --build --push --tag <version> -j 20
```

### Update Registry Configuration

After pushing images to ECR, update the registry configuration in `deployment/inventory/<your-environment>/config.yaml`:

```yaml
registry: "<account-id>.dkr.ecr.<your-region>.amazonaws.com/erag"
tag: "<version>"
setup_registry: false
```

## Service Account and RBAC Configuration

### Create Service Account

Create a service account for administrative access:

```bash
kubectl -n default create serviceaccount $USER-sa
```

### Create Cluster Role Binding

Bind the service account to the `cluster-admin` role:

```bash
kubectl create clusterrolebinding kubeconfig-cluster-admin-token \
  --clusterrole=cluster-admin \
  --serviceaccount=default:$USER-sa
```

### Create Service Account Token Secret

Apply the secret (relies on USER environment variable):

```bash
cd deployment/terraform/aws/nutanix/eks-erag
envsubst < token-admin.yaml | kubectl apply -f -
```

### Retrieve Service Account Token

Extract the token for kubeconfig:

```bash
kubectl -n default get secret kubeconfig-cluster-admin-token -o jsonpath='{.data.token}' | base64 --decode
```

### Update Kubeconfig with Token

Edit your kubeconfig file to use the service account token. Replace the existing authentication method generated by aws-cli with:

```yaml
users:
- name: <your-username>
  user:
    token: <token-from-previous-step>
```

## Storage Configuration

### Set Default Storage Class

Configure the default storage class for persistent volumes:

```bash
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

Verify the default storage class:

```bash
kubectl get storageclass 
```

The default storage class should have `(default)` next to it.

## Pipeline Configuration (Optional)

This section is only applicable if you are using external OpenAI compatible API endpoint

### Configure External LLM Endpoint 

Edit `deployment/pipelines/<your-pipeline>/reference-external-endpoint.yaml` and configure the LLM settings:

```yaml
config:
  endpoint: <endpoint path>
  LLM_MODEL_SERVER: vllm
  LLM_MODEL_SERVER_ENDPOINT: "https://your-vllm-endpoint.com/api"
  LLM_MODEL_NAME: <model_name>
  LLM_VLLM_API_KEY: "your-api-key-here"
```

Replace the placeholder values with your actual LLM endpoint details.

If your endpoint does not have properly configured TLS you can also add `LLM_TLS_SKIP_VERIFY: "True"`

The same can be accomplished on already running cluster by editing gmc the same variables in `gmcconnector` resource in Kubernetes
```
kubectl edit gmconnectors -n chatqa chatqa
```


#### Partner Remote Endpoint Examples

##### Nutanix AI LLM Endpoint

> For complete Nutanix AI endpoint [configuration instructions, refer to the Nutanix AI documentation.](https://portal.nutanix.com/page/documents/details?targetId=Nutanix-Enterprise-AI-v2_0:top-nai-endpoints-page-c.html)

High Level steps: Acquire the Nutanix AI vLLM endpoint details from your Nutanix AI deployment.

1. Navigate to your Nutanix AI management Console
2. Client on "Endpoints" to view the list of available LLM endpoints
3. Select the desired vLLM endpoint to view its details, including the URL, API key, and Sample Request code(see screenshot).

![Nutanix AI Endpoint](./images/nutanix-endpoint.png)

Example Nutanix AI vLLM endpoint configuration:
```bash
curl -k -X 'POST' 'https://nutanix-ai-endpoint.example.com/api/v1/chat/completions' \
 -H "Authorization: Bearer $API_KEY" \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{
      "model": "llama-3-3b",
      "messages": [
        {
          "role": "user",
          "content": "Explain Deep Neural Networks in simple terms"
        }
      ],
      "max_tokens": 256,
      "stream": false
}'

```

Edit `deployment/pipelines/<your-pipeline>/reference-external-endpoint.yaml` and configure the LLM settings:

Example:
```yaml
config:
  endpoint: /v1/chat/completions
  LLM_MODEL_SERVER: vllm
  LLM_MODEL_SERVER_ENDPOINT: "https://nutanix-ai-endpoint.example.com/api"
  LLM_MODEL_NAME: "llama-3-3b"
  LLM_VLLM_API_KEY: "your-api-key-here" 
  LLM_TLS_SKIP_VERIFY: "True"
```
---

## Application Configuration

### Proxy Configuration (if needed)

If your environment requires a proxy, set `K8S_AUTH_PROXY` environment variable:

```bash
export K8S_AUTH_PROXY="http://your-proxy-server:port"
```

### Telemetry Configuration

On EKS it is recommended to disable traces telemetry in `deployment/inventory/<your-environment>/config.yaml`:

```yaml
telemetry:
  enabled: true
  traces:
    enabled: false
```

### Ingress Configuration

EKS doesn't allow using default ports from the service, so you need to remove the following part from `deployment/components/ingress/values.yaml` to unblock ingress' service ports:

```yaml
  hostPort:
    enabled: true
```

Additionally, you need to change service type in `deployment/inventory/<your-environment>/config.yaml` to LoadBalancer:

```yaml
ingress:
  enabled: true
  service_type: LoadBalancer
```

### DNS Configuration

For proper DNS configuration, you need to change the FQDN to the domain that you are planning to use in `deployment/inventory/<your-environment>/config.yaml`:

```yaml
FQDN: "erag.com" # Provide the FQDN for the deployment
```

After deployment, retrieve the LoadBalancer URL:

```bash
kubectl get --namespace ingress-nginx svc/ingress-nginx-controller
```

Configure your DNS provider to create a CNAME record pointing your domain to the LoadBalancer URL. Note that Amazon ELB DNS names do not natively resolve subdomains, so you'll need to configure individual DNS records for each subdomain or use a wildcard DNS entry at your DNS provider.

### TLS Configuration

For detailed TLS configuration options, see [Security Settings](advanced_configuration.md#security-settings) in the Advanced Configuration guide.

## Deployment

### Start deployment

Follow the deployment instructions in the [Deploy the Intel® AI for Enterprise RAG Application](../deployment/README.md#deploy-the-intel-ai-for-enterprise-rag-application-on-top-of-the-prepared-infrastructure) section.

### Verify Deployment

After the installation completes, verify the deployment status and test the pipeline by following the instructions in [Interact with the Deployed Pipeline](../deployment/README.md#interact-with-the-deployed-pipeline).