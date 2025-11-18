# AWS Terraform Configuration for Enterprise RAG (XEON)

This directory contains Terraform configuration files for deploying Enterprise RAG solution on AWS using Xeon-only instances.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** version >= 1.0
4. **SSH Key Pair** created in your target AWS region
5. **Hugging Face Token** for model downloads

## Quick Start

1. **Initialize Terraform:**
   ```bash
   cd deployment/terraform/aws
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
- `provider.tf` - AWS provider configuration

### Template Files
- `templates/inventory.ini.tpl` - Ansible inventory template
- `templates/config-override.yaml.tpl` - Configuration override template
- `templates/user_data.sh.tpl` - EC2 user data script

## Important Notes

- **Instance Type**: Uses Xeon-optimized instances (r8i.32xlarge recommended)
- **SSH Key Setup**: Must exist in your target AWS region before deployment
- **AMI Selection**: Automatically selects latest Ubuntu 24.04 LTS AMI if not specified

## Required Variables

Create a `terraform.tfvars` file with the following variables:

```hcl
# AWS Credentials
aws_access_key = "YOUR_AWS_ACCESS_KEY"
aws_secret_key = "YOUR_AWS_SECRET_KEY"

# Basic Configuration
region         = "us-west-2"
instance_name  = "erag"
ssh_key_name   = "your-key-pair-name"

# Hugging Face Token
hugging_face_token = "YOUR_HUGGING_FACE_TOKEN"

# Solution Version (optional)
solution_version = "release-2.0.0"  # Options: "release-2.0.0", "release-1.5.0", "main"
```

## Optional Variables

```hcl
# Instance Configuration
instance_type     = "r8i.32xlarge"    # CPU optimized instance
root_volume_size  = 100             # GB

# Version Control
solution_version = "release-2.0.0"  # Git tag or branch (default: "release-2.0.0")
                                     # Examples: "release-2.0.0", "release-1.5.0", "main"

# Model Configuration
llm_model_cpu         = ""
embedding_model_name  = ""
reranking_model_name  = ""

# Network Configuration (leave empty to create new resources)
vpc_id            = ""              # Use existing VPC
subnet_id         = ""              # Use existing subnet
security_group_id = ""              # Use existing security group

# SSH Configuration
ssh_user          = "ubuntu"
ssh_allowed_cidr  = "0.0.0.0/0"    # Restrict for production

# Proxy Configuration (if needed)
use_proxy    = false
proxy_scheme = "socks5"
proxy_host   = ""
proxy_port   = 1080

# Resource Naming
resource_prefix = "erag"
fqdn           = "erag.com"

# Tags
tags = {
  Project     = "Enterprise-RAG"
  Environment = "production"
  Terraform   = "true"
}
```

## Network Resources

The configuration automatically creates:
- **VPC** with DNS support enabled
- **Subnet** with public IP assignment
- **Internet Gateway** for internet access
- **Route Table** with internet routing
- **Security Group** with the following rules:
  - SSH (port 22) - restricted to `ssh_allowed_cidr`
  - HTTP (port 80) - open to internet
  - HTTPS (port 443) - open to internet
  - Kubernetes API (port 6443) - VPC internal only
  - All outbound traffic allowed

## Outputs

After successful deployment, Terraform provides:
- `instance_id` - EC2 instance ID
- `instance_public_ip` - Public IP address
- `instance_private_ip` - Private IP address
- `instance_public_dns` - Public DNS name
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
4. **Key Management**: Use AWS Key Management Service for encryption
5. **IAM Roles**: Consider using IAM roles instead of access keys

## Cleanup

To destroy the infrastructure:
```bash
terraform destroy
```

## Troubleshooting

### Common Issues

1. **AMI not found**: Ensure the region supports Ubuntu 24.04 AMIs
2. **Instance type not available**: Choose different availability zone or instance type
3. **Key pair not found**: Verify SSH key pair exists in the target region
4. **Permission denied**: Ensure AWS credentials have required permissions
