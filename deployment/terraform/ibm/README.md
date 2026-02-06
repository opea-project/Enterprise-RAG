# IBM Cloud Terraform Configuration for Enterprise RAG (Intel Gaudi)

This directory contains Terraform configuration files for deploying the Enterprise RAG solution on IBM Cloud using Intel hardware.

## Complete Deployment Guide

**For step-by-step deployment instructions, see: [→ docs/deployment-guide.md](docs/deployment-guide.md)**

The comprehensive deployment guide covers:
- Complete prerequisites checklist with examples
- **IBM Cloud Schematics UI deployment** (recommended for beginners)
- **Terraform CLI deployment** (recommended for advanced users)
- Post-deployment configuration and first-time usage
- Performance tuning and monitoring
- Troubleshooting common issues
- Cleanup and maintenance procedures

## What Gets Deployed

This deployment creates a complete Enterprise RAG infrastructure:

**Infrastructure Components:**
- Intel-powered VPC instance:
  - Gaudi - `gx3d-160x1792x8gaudi3`
  - Xeon - `bx3d-128x640`
- VPC networking with subnet and security groups
- Optimized storage configuration for AI workloads
- Automated software installation and configuration

**AI Software Stack:**
- Intel Gaudi drivers (if necessary) and optimization libraries
- Large Language Model service (Intel optimized)
- Text embedding service for semantic search
- Document reranking for improved relevance
- Vector database for knowledge storage
- RAG orchestration API
- Optional web interface

**Estimated Deployment Time:** 60 minutes

## Quick Technical Reference

### Prerequisites Summary
1. **IBM Cloud Account** with appropriate permissions
2. **IBM Cloud CLI** installed and configured
3. **Terraform** version >= 1.0 (for CLI deployment)
4. **SSH Key Pair** created in IBM Cloud
5. **Hugging Face Token** for model downloads

### Quick CLI Start
```bash


# 1. Initialize Terraform
terraform init

# 2. Configure (see detailed instructions in deployment guide)
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Edit with your values

# 3. Deploy
terraform plan
terraform apply
```

**Essential Variables (minimum required):**
- `api_key` - IBM Cloud API key
- `ssh_key_name` - SSH key name in IBM Cloud  
- `ssh_key` - Path to private SSH key file
- `hugging_face_token` - Token for model downloads

## Configuration Files

### Core Files
- `main.tf` - Main infrastructure resources
- `variables.tf` - Variable definitions
- `outputs.tf` - Output values
- `provider.tf` - IBM Cloud provider configuration

### Template Files
- `templates/inventory.ini.tpl` - Ansible inventory template
- `templates/config-override.yaml.tpl` - Configuration override template
- `templates/user_data.sh.tpl` - Instance initialization script

## Required Variables

Create a `terraform.tfvars` file with the following variables:

```hcl
# IBM Cloud Credentials
api_key = "YOUR_IBM_CLOUD_API_KEY"

# Basic Configuration
region         = "us-south"
instance_name  = "YOUR_IBM_CLOUD_INSTANCE_NAME"
instance_zone  = "us-south-2"
ssh_key_name   = "your-ssh-key-name"
resource_group = "default"

# SSH Configuration
ssh_key = "~/.ssh/ibm_rsa"
ssh_user = "ubuntu"

# Hugging Face Token
hugging_face_token = "YOUR_HUGGING_FACE_TOKEN"

# Solution Version (optional)
solution_version = "release-2.0.1"  # Options: "release-2.0.1", "release-1.5.0", "main"
```

## Optional Variables

```hcl
# Instance Configuration
instance_profile = ""  # Intel instance
# Example gaudi instance: gx3d-160x1792x8gaudi3
# Example xeon instance: bx3d-128x640

boot_volume_size = 250                       # GB

# Version Control
solution_version = "release-2.0.1"         # Git tag or branch (default: "release-2.0.1")
                                            # Examples: "release-2.0.1", "release-1.5.0", "main"

# Model Configuration (Intel Gaudi optimized)
deployment_type       = "hpu"
llm_model_gaudi      = ""
embedding_model_name = ""
reranking_model_name = ""

# Network Configuration (leave empty to create new resources)
vpc            = ""                          # Use existing VPC
subnet         = ""                          # Use existing subnet
security_group = ""                          # Use existing security group

# SSH Configuration
ssh_allowed_cidr = "0.0.0.0/0"              # Restrict for production

# Proxy Configuration (for corporate networks)
use_proxy    = false
proxy_scheme = "socks5"
proxy_host   = ""
proxy_port   = 1080

# Resource Naming
resource_prefix = "erag"
fqdn           = "erag.com"
```

## Network Resources

The configuration automatically creates:
- **VPC** with DNS support enabled
- **Subnet** with internet access via Public Gateway
- **Public Gateway** for outbound connectivity
- **Security Group** with the following rules:
  - SSH (port 22) - restricted to `ssh_allowed_cidr`
  - HTTP (port 80) - open to internet
  - HTTPS (port 443) - open to internet
  - Kubernetes API (port 6443) - VPC internal only
  - All outbound traffic allowed
- **Floating IP** for external access

## Important Notes

- **Intel Gaudi Availability**: Gaudi instances are only available in specific zones: `us-south-2`, `eu-de-1`, `us-east-2`, `us-east-3`
- **SSH Key Setup**: Must be created in IBM Cloud Console before deployment
- **API Key**: Obtain from IBM Cloud Console → Manage → Access (IAM) → API keys

## Outputs

After successful deployment, Terraform provides:
- `instance_id` - Virtual Server instance ID
- `floating_ip` - Public IP address
- `instance_private_ip` - Private IP address
- `vpc_id` - VPC ID
- `subnet_id` - Subnet ID
- `security_group_id` - Security Group ID
- `ssh_connection_command` - Ready-to-use SSH command

## Security Considerations

1. **SSH Access**: Restrict `ssh_allowed_cidr` to your IP range
2. **Credentials**: Never commit `terraform.tfvars` with sensitive data
3. **State File**: Store Terraform state securely (consider remote backend)
4. **API Key Management**: Use IBM Cloud IAM for proper access control
5. **Corporate Networks**: Configure proxy settings for restricted environments

## Cleanup

To destroy the infrastructure:
```bash
terraform destroy
```

## Troubleshooting

### Common Issues

1. **SSH key not found**: Verify SSH key exists in IBM Cloud Console for your region
2. **Instance type not available**: Ensure Intel Gaudi instances are available in your chosen zone
3. **API key permissions**: Verify API key has VPC Infrastructure and Resource Group access
4. **Resource group not found**: Check resource group name and API key permissions
5. **Proxy issues**: Verify proxy settings for corporate network deployments
