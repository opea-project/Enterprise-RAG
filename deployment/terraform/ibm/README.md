# IBM Cloud Terraform Configuration for Enterprise RAG (Intel Gaudi)

This directory contains Terraform configuration files for deploying Enterprise RAG solution on IBM Cloud using Intel Gaudi accelerators.

## Prerequisites

1. **IBM Cloud Account** with appropriate permissions
2. **IBM Cloud CLI** installed and configured
3. **Terraform** version >= 1.0
4. **SSH Key Pair** created in IBM Cloud
5. **Hugging Face Token** for model downloads

## Quick Start

1. **Initialize Terraform:**
   ```bash
   cd deployment/terraform/ibm
   terraform init
   ```

2. **Create terraform.tfvars file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Plan the deployment:**
   ```bash
   terraform plan
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply
   ```

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
instance_name  = "erag-gaudi"
instance_zone  = "us-south-2"
ssh_key_name   = "your-ssh-key-name"
resource_group = "default"

# SSH Configuration
ssh_key = "~/.ssh/ibm_rsa"
ssh_user = "ubuntu"

# Hugging Face Token
hugging_face_token = "YOUR_HUGGING_FACE_TOKEN"

# Model Configuration (Intel Gaudi optimized)
deployment_type       = "hpu"
llm_model_gaudi      = ""
embedding_model_name = ""
reranking_model_name = ""
```

## Optional Variables

```hcl
# Instance Configuration
instance_profile = "gx3d-160x1792x8gaudi3"  # Intel Gaudi instance
boot_volume_size = 250                       # GB

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

## Generated Files

The configuration generates:
- `../../inventory.ini` - Ansible inventory file
- `../../config-override.yaml` - Configuration override file

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
