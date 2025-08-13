# Enterprise RAG Infrastructure as Code (IBM Cloud)

This directory contains Terraform Infrastructure as Code (IaC) for deploying Enterprise RAG solution on IBM Cloud using Intel Gaudi accelerators.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installing Terraform](#installing-terraform)
- [IBM Cloud Setup](#ibm-cloud-setup)
- [Infrastructure Overview](#infrastructure-overview)
- [Variables Reference](#variables-reference)
- [Quick Start](#quick-start)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)

## Prerequisites

- IBM Cloud account with appropriate permissions
- SSH key pair for instance access
- Hugging Face token for model downloads
- Terraform >= 1.0

## Installing Terraform

### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common

# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add official HashiCorp repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/hashicorp.list

# Update and install Terraform
sudo apt update
sudo apt-get install terraform

# Verify installation
terraform version
```
## IBM Cloud Setup

### Obtaining IBM Cloud API Key

1. **Log in to IBM Cloud Console**
   - Visit [cloud.ibm.com](https://cloud.ibm.com)
   - Sign in with your IBM ID

2. **Navigate to API Keys**
   - Click on "Manage" → "Access (IAM)"
   - Select "API keys" from the left menu
   - Click "Create an IBM Cloud API key"

3. **Create API Key**
   - Enter a descriptive name (e.g., "terraform-user-key")
   - Add description: "Terraform key for Enterprise RAG deployment"
   - Click "Create"

4. **Download and Secure**
   - **Important**: Download or copy the API key immediately
   - Store securely - you cannot retrieve it later
   - Consider using environment variables instead of hardcoding

### Setting Up SSH Keys

You can generate and manage SSH keys either through the command line or IBM Cloud UI:

#### Option 1: Generate SSH Key Pair via IBM Cloud UI
1. **Navigate to SSH Keys**:
   - Go to IBM Cloud Console
   - Navigate to "Infrastructure" → "Compute" → "SSH keys"
   - Click "Create SSH key"

2. **Generate New Key Pair**:
   - Select "Generate a new key pair"
   - Enter a name for your SSH key (e.g., "erag-ssh-key")
   - Click "Generate SSH key"
   - **Important**: Download the private key immediately and save it securely
   - Note the location where you save it (e.g., `~/.ssh/ibm_rsa`)

#### Option 2: Adding Existing Public Key to IBM Cloud
If you already have an SSH key pair:
1. **Navigate to SSH Keys**:
   - Go to IBM Cloud Console  
   - Navigate to "Infrastructure" → "Compute" → "SSH keys"
   - Click "Create SSH key"

2. **Upload Existing Public Key**:
   - Select "Provide existing public key"
   - Enter a name for your SSH key
   - Paste your public key content (`cat ~/.ssh/ibm_rsa.pub`)

## Infrastructure Overview

This Terraform configuration creates the following IBM Cloud resources:

### Core Infrastructure
- **VPC**: Virtual Private Cloud (creates new or uses existing)
- **Subnet**: Private subnet with CIDR block (creates new or uses existing)
- **Public Gateway**: For outbound internet access (one per VPC)
- **Security Group**: Firewall rules for SSH and application access
- **Instance**: IBM Cloud Virtual Server with Intel Gaudi accelerators
- **Floating IP**: Public IP for external access

### Deployment Features
- **Automated Installation**: Runs Enterprise RAG installation script
- **Proxy Support**: Corporate proxy configuration for restricted environments
- **Flexible Infrastructure**: Uses existing or creates new network resources
- **AI Accelerator Ready**: Configured for Intel Gaudi AI processing units

## Variables Reference

### Required Variables

| Variable | Description | Type | Example |
|----------|-------------|------|---------|
| `api_key` | IBM Cloud API key | `string` | `"your-api-key-here"` |
| `region` | IBM Cloud region | `string` | `"us-south"`, `"eu-de"` |
| `ssh_key` | Path to SSH private key | `string` | `"~/.ssh/ibm_rsa"` |
| `ssh_key_name` | Name of SSH key in IBM Cloud | `string` | `"my-ssh-key"` |
| `instance_name` | Name for the instance | `string` | `"erag-instance"` |
| `instance_zone` | IBM Cloud availability zone | `string` | `"us-south-1"`, `"eu-de-1"` |
| `resource_group` | IBM Cloud resource group | `string` | `"default"` |
| `hugging_face_token` | Hugging Face API token | `string` | `"your-hugging-face-token"` |
⚠️ **Important**: Gaudi instances are only available in the following IBM Cloud zones: `us-south-2`, `eu-de-1`, `us-east-2`, and `us-east-3`.

### Optional Infrastructure Variables

| Variable | Description | Type | Default | Notes |
|----------|-------------|------|---------|-------|
| `vpc` | Existing VPC name | `string` | `""` | Leave empty to create new |
| `subnet` | Existing subnet name | `string` | `""` | Leave empty to create new |
| `security_group` | Existing security group name | `string` | `""` | Leave empty to create new |
| `instance_profile` | Instance type/profile | `string` | `"gx3d-160x1792x8gaudi3"` | Gaudi AI accelerator profile |
| `osimage` | Operating system image | `string` | `"ibm-ubuntu-24-04-2-minimal-amd64-5"` | Ubuntu 24.04 minimal |
| `boot_volume_size` | Boot disk size in GB | `number` | `100` | Range: 100-250 GB |

### Network Security Variables

| Variable | Description | Type | Default |
|----------|-------------|------|---------|
| `ssh_allowed_cidr` | CIDR block for SSH access | `string` | `"0.0.0.0/0"` |
| `ssh_user` | SSH username | `string` | `"ubuntu"` |

### Proxy Configuration (Corporate Networks)

| Variable | Description | Type | Default |
|----------|-------------|------|---------|
| `use_proxy` | Enable proxy for connections | `bool` | `false` |
| `proxy_scheme` | Proxy protocol | `string` | `"socks5"` |
| `proxy_host` | Proxy server hostname | `string` | `""` |
| `proxy_port` | Proxy server port | `number` | `1080` |

### Enterprise RAG Configuration

| Variable | Description | Type | Default | Required |
|----------|-------------|------|---------|----------|
| `fqdn` | Fully qualified domain name | `string` | `"erag.com"` | No |
| `deployment_type` | Model deployment target | `string` | `"hpu"` | No |
| `llm_model_cpu` | CPU-based LLM model name | `string` | `""` | No |
| `llm_model_gaudi` | Gaudi-based LLM model name | `string` | `""` | No |
| `embedding_model_name` | Embedding model name | `string` | `""` | No |
| `reranking_model_name` | Reranking model name | `string` | `""` | No |

### Resource Naming

| Variable | Description | Type | Default |
|----------|-------------|------|---------|
| `resource_prefix` | Prefix for resource names | `string` | `"erag"` |

## Quick Start
### 1. Create Configuration File
Copy and customize the configuration:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# Required variables
api_key = "your-ibm-cloud-api-key"
region = "us-south"
ssh_key = "~/.ssh/ibm_rsa"
ssh_key_name = "my-ssh-key"
instance_name = "my-erag-instance"
instance_zone = "us-south-1"
resource_group = "default"

# Optional: Use existing infrastructure
# vpc = "my-existing-vpc"
# subnet = "my-existing-subnet"
# security_group = "my-existing-sg"

# Optional: Hugging Face token for model downloads
hugging_face_token = "hf_your_token_here"

# Optional: Corporate proxy settings
# use_proxy = true
# proxy_host = "proxy.company.com"
# proxy_port = 8080
```

### 2. Initialize and Deploy
```bash
# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy infrastructure
terraform apply
```

### 3. Access Your Deployment
After successful deployment:
```bash
# Get the public IP
terraform output floating_ip

# SSH to the instance
# If using a proxy, configure your SSH client accordingly (e.g., ProxyJump or ProxyCommand)
# Add to ~/.ssh/config
# Host ibm
#  Hostname <floating_ip>
#  User ubuntu
#  ProxyCommand /usr/bin/nc -x <proxy_server>:1080 %h %p
#  IdentityFile /home/<user>/.ssh/<private_key>
ssh ibm

# Check Enterprise RAG status
kubectl get pods -A
```

⚠️ **Important**: Default passwords can be found in /hom/$USER/ansible-logs

## Advanced Configuration

### Using Existing Infrastructure
To deploy into existing VPC infrastructure:

```hcl
# terraform.tfvars
vpc = "my-existing-vpc"
subnet = "my-existing-subnet" 
security_group = "my-existing-security-group"
```

### Corporate Proxy Setup
For deployments behind corporate firewalls:

```hcl
# terraform.tfvars
use_proxy = true
proxy_scheme = "http"  # or "socks5"
proxy_host = "proxy.company.com"
proxy_port = 8080
ssh_allowed_cidr = "10.0.0.0/8"  # Restrict SSH to internal networks
```

### Custom Model Configuration
To use specific AI models:

```hcl
# terraform.tfvars
deployment_type = "hpu"  # or "cpu"
llm_model_gaudi = "mistralai/Mixtral-8x7B-Instruct-v0.1"
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
reranking_model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
fqdn = "my-erag.company.com"
```

### Boot volume scaling
If needed adjust boot volume size:

```hcl
# terraform.tfvars
boot_volume_size = 250  # Maximum boot disk size
```

## Troubleshooting

### Common Issues

#### 1. SSH Key Not Found
```
Error: SSH key 'key-name' not found
```
**Solution**: 
- Verify key exists in IBM Cloud Console
- Check `ssh_key_name` matches exactly
- Upload public key to IBM Cloud

#### 2. API Key Permissions
```
Error: Insufficient permissions
```
**Solution**:
- Verify API key has VPC Infrastructure permissions
- Check resource group access
- Contact IBM Cloud administrator

#### 3. Resource Group Not Found
```
Error: Resource group 'group-name' not found
```
**Solution**:
- List available resource groups: `ibmcloud resource groups`
- Use correct resource group name
- Check API key has access to the resource group

#### 4. Proxy Connection Issues
```
Error: Connection timeout during installation
```
**Solution**:
- Verify proxy settings are correct
- Check corporate firewall allows necessary traffic
- Test proxy connectivity manually

### Log Access

```bash
# SSH to the instance
# If using a proxy, configure your SSH client accordingly (e.g., ProxyJump or ProxyCommand)
# Add to ~/.ssh/config
# Host ibm
#  Hostname <floating_ip>
#  User ubuntu
#  ProxyCommand /usr/bin/nc -x <proxy_server>:1080 %h %p
#  IdentityFile /home/<user>/.ssh/<private_key>
ssh ibm

# Check installation logs
tail -f /var/log/enterprise-rag-install.log

# Check Kubernetes status
kubectl get nodes
kubectl get pods -A

# Check system status
systemctl status kubelet
systemctl status containerd
```

## Cleanup

### Destroy Infrastructure
```bash
# Review what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy

# Force cleanup if needed
terraform destroy -auto-approve
```

### Manual Cleanup
If Terraform destroy fails, manually remove:

1. **In IBM Cloud Console**:
   - Delete floating IPs
   - Delete instances
   - Delete security groups (if created)
   - Delete subnets (if created)
   - Delete VPC (if created)

2. **Clean Terraform State**:
```bash
rm -rf .terraform/
rm terraform.tfstate*
```

## Support

For issues and questions:

1. **Check IBM Cloud Status**: [cloud.ibm.com/status](https://cloud.ibm.com/status)
2. **Review Terraform Logs**: Enable with `TF_LOG=DEBUG terraform apply`
3. **IBM Cloud CLI**: Use `ibmcloud` commands for manual verification
4. **Enterprise RAG Documentation**: Check main repository documentation

## Security Considerations

- **API Key Security**: Store API keys securely, use environment variables
- **SSH Keys**: Protect private keys, use strong passphrases
- **Network Access**: Restrict SSH access with `ssh_allowed_cidr`
- **Proxy Settings**: Ensure proxy credentials are secure
- **Resource Groups**: Use appropriate resource groups for access control
