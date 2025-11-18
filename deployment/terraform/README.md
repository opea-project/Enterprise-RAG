# Terraform Infrastructure for Intel® AI for Enterprise RAG

This directory contains Terraform configurations for deploying Intel® AI for Enterprise RAG solution on multiple cloud platforms.

## Supported Platforms

### **AWS (CPU)**
Deploy Intel® AI for Enterprise RAG on AWS using CPU-optimized instances.

**Directory**: [`aws/`](./aws/)
- **Instance Type**: r8i.48xlarge (CPU optimized)
- **Operating System**: Ubuntu 24.04 LTS

**[AWS Documentation](./aws/README.md)**

### **IBM Cloud (Intel Gaudi)**
Deploy Intel® AI for Enterprise RAG on IBM Cloud using Intel Gaudi AI accelerators.

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

## Version Management

The deployment supports specifying a particular version or tag of the Intel® AI for Enterprise RAG solution:

```hcl
# In terraform.tfvars
solution_version = "release-2.0.0"    # Deploy specific tag (default)
solution_version = "release-1.5.0"    # Deploy older version
solution_version = "main"             # Deploy from main branch
```

This allows you to:
- Deploy specific released versions for stability (e.g., release-2.0.0, release-1.5.0)
- Test new features from specific branches (e.g., main)

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

For general Intel® AI for Enterprise RAG questions, check the main repository documentation.
