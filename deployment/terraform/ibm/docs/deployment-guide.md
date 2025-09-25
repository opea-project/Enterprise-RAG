# Enterprise RAG Deployment Guide

## What is Enterprise RAG?

Intel® AI for Enterprise RAG (Retrieval-Augmented Generation) is a comprehensive solution that combines large language models with enterprise knowledge bases to provide accurate, contextual AI responses. This deployment creates a complete RAG infrastructure on IBM Cloud using Intel Gaudi accelerators for optimized AI inference performance.

**Key Features:**
- Intel Gaudi3 accelerated inference
- Vector database integration
- Document processing pipeline  
- Enterprise-grade security
- Scalable architecture

**Dedicated for:**
- Enterprise AI chatbots and Q&A systems
- Document analysis and knowledge extraction
- Intelligent search and retrieval systems
- Context-aware AI applications

## Prerequisites

Before deploying Enterprise RAG, ensure you have the essential requirements ready:

### 1. IBM Cloud API Key (Required)
**What it is:** Your authentication credentials for IBM Cloud
**How to get it:**
1. Go to [IBM Cloud API Keys](https://cloud.ibm.com/iam/apikeys)
2. Click "Create"
3. Give it a name like "Enterprise-RAG-Key"
4. Copy and save the key securely

### 2. IBM Cloud CLI Installation (Required)
**What it is:** Command-line tool for managing IBM Cloud resources  
**How to install:** Follow the [official IBM Cloud CLI installation guide](https://cloud.ibm.com/docs/cli?topic=cli-getting-started)

**After installation, login with your API key:**
```bash
ibmcloud login --apikey YOUR_API_KEY -r <us-south|us-east|eu-de|eu-gb>
```

### 3. IBM Cloud SSH Key (Required)
**What it is:** Your SSH key for secure access to the virtual machine  
**How to get it:**
```bash
# Generate a new key pair (if you don't have one)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ibm-rag-key

# Upload the public key to IBM Cloud via CLI
ibmcloud is key-create my-rag-key @~/.ssh/ibm-rag-key.pub
```
**Or upload via UI:** [VPC SSH Keys console](https://cloud.ibm.com/vpc-ext/compute/sshKeys)

**Example values:**
- SSH key name: `my-rag-key`
- Private key path: `~/.ssh/ibm-rag-key`

### 4. Hugging Face Token (Required)
**What it is:** Authentication token for downloading AI models from Hugging Face  
**How to get it:**
1. Create account at [huggingface.co](https://huggingface.co)
2. Go to Settings → Access Tokens
3. Create a new token with "Read" permissions
4. Copy and save the token
5. Add access for model: mistralai/Mixtral-8x22B-Instruct-v0.1. Based on [documentation](https://huggingface.co/docs/hub/models-gated)
6. Confirm access has been approved

### 5. Resource Group (Required)
**What it is:** Organizational container for your IBM Cloud resources  
**Options:**
- Use existing: `Default` (most common)
- Create new: [Resource Groups console](https://cloud.ibm.com/account/resource-groups)

## Deployment Methods

You can deploy Enterprise RAG using two methods:

### Method 1: IBM Cloud Catalog UI (Recommended for Beginners)

The UI deployment provides a visual, guided experience through the IBM Cloud console with form-based configuration and built-in validation.

#### Step 1: Access IBM Cloud Catalog
1. Go to [IBM Cloud Console](https://cloud.ibm.com)
2. Navigate to "Catalog" → "Software" or "Community registry"
3. Search for "Intel AI Enterprise RAG" and click on the tile

#### Step 2: Select Standard Variation
1. On the variations page select "Standard"
2. Click "Add to project" in the bottom right

#### Step 3: Configure Project

#### Option A: Create New Project
1. Select "Create new"
2. Fill in the project details:
   - **Name:** Your project name (e.g., "enterprise-rag-project")
   - **Description:** Brief description of your project
   - **Configuration name:** Name for this configuration (e.g., "standard-config")
   - **Region:** Select from dropdown
   - **Resource group:** Select from dropdown

#### Option B: Add to Existing Project
1. Select "Add to existing"
2. **Select a project:** Choose from dropdown
3. **Configuration name:** Enter a name for this configuration

After selecting your option, click **"Add"** in the bottom right.

#### Step 4: Configure Security & Architecture
You'll be taken to the deployment configuration page. First, in the **Security** section, add your IBM Cloud API key, then click **"Next"**.

On the **Configure architecture** page, edit all required inputs (turn on **Advanced** to access optional inputs). Configure the following Enterprise RAG specific variables:

**Required Variables:**
- **SSH key name**: Select your SSH key (must exist in IBM Cloud)
- **SSH private key**: Paste the content of your private key file
- **IBM Cloud region**: Select your deployment region
- **Instance zone**: Choose availability zone within the region
- **Hugging Face token**: Your HF token for model access
- **Instance name**: Descriptive name for your RAG instance
- **Resource group**: Target resource group for deployment

**Advanced Configuration (click "Advanced" toggle):**
- **Instance profile**: Select `gx3d-160x1792x8gaudi3` for Intel Gaudi acceleration
- **Boot volume size**: Storage size in GB (recommended: 250GB)
- **Deployment type**: Set to `hpu` for Hardware Processing Unit optimization
- **FQDN**: Choose your fqdn
- **SSH allowed CIDR**: Network range for SSH access (use `0.0.0.0/0` for testing only)

> **Note:** For Intel® Gaudi® AI accelerator deployments, ensure you select a region with Gaudi availability: `us-east`, `us-south`, or `eu-de`

#### Step 5: Save and Deploy
1. Click **"Save"** in the top-right to save your configuration
2. Click **"Validate"** to check your configuration - you'll see "Validating changes..." and "Generating plan..." which takes 2-3 minutes
3. Once you see **"Validation successful"**, enter a comment and click **"Approve"** to enable the Deploy button
4. Click **"Deploy"** in the bottom-right
5. Monitor **"Deploying changes..."** progress and click **"View logs"** to see detailed deployment logs (deployment takes ~60 minutes for Enterprise RAG)

6. Once deployment completes, you'll see **"Deployment successful"** with **"Changes deployed successfully"**

7. Click on **"Changes deployed successfully"** to view deployment details

8. Click on the **"Logs"** tab to view complete deployment logs

#### Step 6: View Deployment Outputs
To view deployment outputs including instance IP and RAG endpoints:
1. Click **Navigation Menu** (☰) in the top-left
2. Select **Projects**
3. Choose your project from the list
4. Click on **Configurations**
5. Click on your deployment name

### Method 2: Terraform CLI (Recommended for Advanced Users)

CLI deployment using infrastructure-as-code provides maximum control and enables automation.

#### Step 1: Initialize Terraform
```bash
# Initialize Terraform (downloads required providers)
terraform init
```

#### Step 2: Configure Variables
Create and configure your deployment settings:

```bash
# Copy the example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit with your preferred editor
vim terraform.tfvars
```

**Required Configuration (terraform.tfvars):**
```hcl
# IBM Cloud Authentication
api_key = "your-api-key-from-step-1"

# Basic Configuration
region         = "us-south"                    # Your preferred region
instance_name  = "my-enterprise-rag"          # Descriptive name for your instance
instance_zone  = "us-south-1"                 # Availability zone
ssh_key_name   = "my-rag-key"                 # SSH key name from step 3
resource_group = "Default"                    # Your resource group

# SSH Configuration  
ssh_key  = "~/.ssh/ibm-rag-key"              # Path to your private key
ssh_user = "ubuntu"                           # Default user for Ubuntu images

# AI Configuration
hugging_face_token = "hf_your-token-here"    # Your HF token from step 4

# Network Security (IMPORTANT!)
# For Development/Testing:
ssh_allowed_cidr = "0.0.0.0/0"
# For Production - use your organization's IP range:
# ssh_allowed_cidr = "203.0.113.0/24"
```

**Optional Advanced Configuration:**
```hcl
# Intel Gaudi Instance Configuration
instance_profile = "gx3d-160x1792x8gaudi3"   # Intel Gaudi3 optimized
boot_volume_size = 250                        # Storage in GB

deployment_type       = "hpu"                 # Hardware Processing Unit

# Corporate Network Proxy (if required)
use_proxy    = false
proxy_scheme = "socks5" 
proxy_host   = "proxy.company.com"
proxy_port   = 1080

# Resource Naming
resource_prefix = "erag"
fqdn           = "mycompany.com"
```

#### Step 3: Validate Configuration
```bash
# Check configuration syntax and plan
terraform plan

# Review the planned changes carefully
# Ensure all values look correct before proceeding
```

#### Step 4: Deploy
```bash
# Apply the configuration (creates all resources)
terraform apply

# Type 'yes' when prompted to confirm
# Deployment takes ~60 minutes
```

#### Step 5: Monitor Deployment
```bash
# Watch deployment progress
terraform apply -auto-approve
```

#### Step 6: Access Your RAG System
After successful deployment:

```bash
# Get the public IP address
terraform output instance_public_ip

# SSH into your RAG instance
ssh -i ~/.ssh/ibm-rag-key ubuntu@$(terraform output -raw instance_public_ip)
```

### Verify Installation

After deployment completion, follow these steps to verify your Enterprise RAG installation is working correctly.

#### Step 1: SSH Access and Pod Verification

1. **SSH into your RAG instance:**
   ```bash
   # Use the SSH connection command from deployment outputs
   ssh -i ~/.ssh/your-key ubuntu@<FLOATING_IP>
   ```

2. **Verify all pods are running:**
   ```bash
   # Check all pods across all namespaces. All pods should show STATUS: Running or Completed
   kubectl get po -A
   ```

#### Step 2: Access Enterprise RAG Web UI


1. **Retrieve login credentials:**
   ```bash
   # Get default credentials from ansible logs
   cat ~/ansible-logs/default.credentials.txt
   ```

2. **Navigate to the main UI:**
   ```
   URL: https://<your-fqdn>
   Default: https://enterprise-rag.local
   ```

3. **Login process:**
   - Click "Login" - you'll be redirected to Keycloak
   - Use credentials from `~/ansible-logs/default.credentials.txt`
   - **Username:** `erag-admin`
   - **Password:** `<from-credentials-file>`

4. **After successful login:**
   - You'll be redirected to the ChatQA UI
   - You should see the document upload interface
   - Chat interface should be ready for queries

#### Step 4: Test RAG Functionality

1. **Upload a test document:**
   - Click "Upload Documents" in the UI
   - Upload a PDF, DOCX, or TXT file
   - Wait for processing completion (green checkmark)

2. **Test a query:**
   - In the chat interface, ask a question about your uploaded document
   - Example: "What is the main topic of the uploaded document?"
   - Verify you receive a contextual response

3. **Verify response quality:**
   - Response should reference your uploaded content
   - Check for source citations in the response
   - Response time should be under 30 seconds

#### Step 5: Access Monitoring and Analytics
1. **Retrieve login credentials:**
   ```bash
   # Get default credentials from ansible logs
   cat ~/ansible-logs/default.credentials.yaml
   ```
2. **Grafana Dashboard (Telemetry Stack):**
   ```
   URL: https://grafana.<your-fqdn>
   Default: https://grafana.enterprise-rag.local

   Login: admin / <grafana-password-from-credentials-file>
   ```

3. **Keycloak Admin Console:**
   ```
   URL: https://auth.<your-fqdn>
   Default: https://auth.enterprise-rag.local

   Login: admin / <keycloak-password-from-credentials-file>
   ```

   **Verify:**
   - User management is accessible
   - RAG realm is configured
   - Client applications are registered

**Quick Access Links:**
- **Main UI**: `https://<your-fqdn>`
- **Grafana**: `https://grafana.<your-fqdn>`
- **Keycloak**: `https://auth.<your-fqdn>`

## Cleanup

### UI Deployment Cleanup
1. Go to IBM Cloud Console → Resources
2. Find your RAG resources
3. Select and delete each resource
4. Confirm deletion

### CLI Deployment Cleanup
```bash
# Destroy all resources created by Terraform
terraform destroy

# Type 'yes' when prompted
# This will remove ALL resources and cannot be undone
```

**Important:** Cleanup removes all data permanently. Backup any important information before cleanup.

## Next Steps

After successful deployment:

1. **Upload Documents:** Use the ingestion API to add your knowledge base
2. **Configure Security:** Implement proper authentication and network security
3. **Monitor Performance:** Set up logging and monitoring for production use
4. **Scale Resources:** Adjust instance sizes based on usage patterns
