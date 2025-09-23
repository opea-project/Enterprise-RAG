# Terraform Infrastructure for Enterprise RAG

This directory contains Terraform configurations for deploying Enterprise RAG solution on multiple cloud platforms.

## Supported Platforms

### **AWS (CPU)**
Deploy Enterprise RAG on AWS using CPU-optimized instances.

**Directory**: [`aws/`](./aws/)
- **Instance Type**: r8i.48xlarge (CPU optimized)
- **Operating System**: Ubuntu 24.04 LTS

**[AWS Documentation](./aws/README.md)**

### **IBM Cloud (Intel Gaudi)**
Deploy Enterprise RAG on IBM Cloud using Intel Gaudi AI accelerators.

**Directory**: [`ibm/`](./ibm/)
- **Instance Type**: gx3d-160x1792x8gaudi3 (Intel Gaudi accelerators)
- **Operating System**: Ubuntu 24.04 LTS

**[IBM Cloud Documentation](./ibm/README.md)**

## Quick Start

1. **Choose your platform** and navigate to the appropriate directory:
   ```bash
   cd aws/     # For AWS deployment
   cd ibm/     # For IBM Cloud deployment
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your credentials and settings
   ```

4. **Deploy infrastructure**:
   ```bash
   terraform plan
   terraform apply
   ```

## Shared Resources

### Templates
The [`templates/`](./templates/) directory contains shared Terraform templates used by both platforms:
- `inventory.ini.tpl` - Ansible inventory template
- `config-override.yaml.tpl` - Configuration override template

### Scripts
The [`scripts/`](./scripts/) directory contains deployment scripts:
- `run_install.sh` - Unified installation script for both platforms

## Platform Comparison

| Feature | AWS | IBM Cloud |
|---------|-----|-----------|
| **Compute** | r8i.48xlarge (CPU) | gx3d-160x1792x8gaudi3 (AI) |
| **Performance** | High CPU performance | AI-accelerated processing |
| **Proxy Support** | Yes | Yes |
| **Auto Install** | Yes | Yes |

## Prerequisites

Before deploying on either platform, ensure you have:

1. **Terraform** >= 1.0 installed
2. **Cloud CLI** tools (AWS CLI or IBM Cloud CLI)
3. **SSH key pair** created in your target cloud
4. **API credentials** configured
5. **Hugging Face token** for model downloads

## Destroy Infrastrucutre

```bash
terraform destroy
```

## Security Notes

**Important Security Considerations**:
- Never commit `terraform.tfvars` files with credentials
- Restrict SSH access (`ssh_allowed_cidr`) for production deployments
- Use appropriate IAM/access policies for cloud resources
- Store Terraform state files securely (consider remote backends)

## Support

For platform-specific issues, refer to the individual README files:
- **AWS Issues**: See [aws/README.md](./aws/README.md#troubleshooting)
- **IBM Cloud Issues**: See [ibm/README.md](./ibm/README.md#troubleshooting)

For general Enterprise RAG questions, check the main repository documentation.
