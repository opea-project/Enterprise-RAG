# Intel® AI for Enterprise RAG Deployment Guide

This document details the deployment of Intel® AI for Enterprise RAG using the unified installer script. By default, the guide assumes a Xeon deployment. If your hardware stack contains Gaudi, modify configuration values accordingly to deployment instructions.

## Table of Contents

1. [Intel® AI for Enterprise RAG Deployment](#intel-ai-for-enterprise-rag-deployment)
   1. [Prerequisites](#prerequisites)
   2. [Virtual Environment Setup](#virtual-environment-setup)
   3. [Configuration Setup](#configuration-setup)
   4. [Validate Hardware Requirements](#validate-hardware-requirements)
   5. [Complete Stack Deployment (Recommended)](#complete-stack-deployment-recommended)
   6. [Manual Step-by-Step Deployment](#manual-step-by-step-deployment)
   7. [Update Application Components](#update-application-components)
   8. [Create and Restore Backups](#create-and-restore-backups)
2. [Interact with ChatQnA](#interact-with-chatqna)
   1. [Test Deployment](#test-deployment)
   2. [Access the UI/Grafana](#access-the-uigrafana)
   3. [UI Credentials for the First Login](#ui-credentials-for-the-first-login)
   4. [Credentials for Grafana and Keycloak](#credentials-for-grafana-and-keycloak)
   5. [Credentials for Vector Store](#credentials-for-vector-store)
   6. [Credentials for Enhanced Dataprep Pipeline (EDP)](#credentials-for-enhanced-dataprep-pipeline-edp)
   7. [Data Ingestion, UI and Telemetry](#data-ingestion-ui-and-telemetry)
   8. [Configure Single Sign-On Integration Using Microsoft Entra ID](#configure-single-sign-on-integration-using-microsoft-entra-id)
3. [Remove the Installation](#remove-the-installation)

---

# Intel® AI for Enterprise RAG Deployment

Intel® AI for Enterprise RAG provides a unified installer script (`installer.sh`) that automates the complete deployment workflow:

0. **Prerequisites setup** (passwordless sudo, configuration files)
1. **Virtual environment initialization** (Python dependencies and Ansible)
2. **Hardware validation** (recommended before deployment)
3. **System configuration** (dependencies, tools, services)
4. **Kubernetes cluster deployment** (optional - if you don't have one)
5. **Infrastructure components installation** (storage, operators, backup tools)
6. **Enterprise RAG application deployment** (complete application stack)
7. **Update and maintenance** (models, configurations, backups)
8. **Cleanup and removal** (when no longer needed)

The installer script provides both automated complete stack deployment and granular step-by-step control for advanced users.

## Prerequisites

### Passwordless Sudo Configuration

The installer requires passwordless sudo for system-level operations. Configure this by running:

```bash
echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/erag-installer
```

> [!WARNING]
> This grants passwordless sudo access. For production environments, consider limiting sudo privileges to specific commands needed by the installer.

#### Alternative Password Management

If passwordless sudo is not desired or possible, you can manage sudo passwords through Ansible inventory variables:

**Option 1: Using ansible_become_pass in inventory**
```ini
[all]
server1 ansible_host=192.168.1.10 ansible_become_pass=your_sudo_password
server2 ansible_host=192.168.1.11 ansible_become_pass=your_sudo_password
```

**Option 2: Using Ansible Vault for encrypted passwords**
Ansible Vault can be used to encrypt sensitive password information in inventory files for enhanced security.

### System Requirements

- **Operating System**: Ubuntu/Debian (tested on Ubuntu 20.04+)
- **Python**: Python 3.8 or higher with venv module
- **Connectivity**: Internet access for downloading dependencies
- **Hardware**: See hardware validation section for specific requirements

## Virtual Environment Setup

Initialize the Python virtual environment with all required dependencies:

```bash
cd deployment
./installer.sh setup python-env
```

This command will:
- Create a Python virtual environment (`erag-venv`)
- Install pip and upgrade it to the latest version
- Install Ansible and all Python dependencies from `requirements.txt`
- Install required Ansible collections from `requirements.yaml`

**After initialization, activate the virtual environment:**

```bash
source erag-venv/bin/activate
```

> **⚠️ Important**: 
> 
> If you see `Failed to import the required Python library (kubernetes)` or similar import errors, 
> check that:
> 1. You activated the virtual environment before running installer commands
> 2. You added `ansible_python_interpreter` to your inventory for localhost


This ensures Ansible uses the virtual environment's Python for localhost tasks, providing better package isolation.

### Shell Auto-Completion (Optional)

Enable tab completion for the installer script to improve usability:

```bash
# For Bash
source scripts/installer-completion.bash

# For Zsh
source scripts/_installer.sh
```

For permanent setup, see [COMPLETION.md](COMPLETION.md) for detailed installation instructions.

## Configuration Setup

### Option 1: Interactive Configuration (Recommended for first-time users)

Generate configuration files interactively:

```bash
./installer.sh setup config
```

To create configuration in a custom directory:

```bash
./installer.sh setup config /path/to/new-config-directory
```

The interactive setup will:
1. **Prompt for inventory type selection:**
   - **localhost**: For deploying applications on an existing Kubernetes cluster
   - **sample**: For multi-node cluster deployment
2. **Copy configuration files:**
   - `config.yaml` (always from `inventory/sample/` - shared configuration)
   - `inventory.ini` (from selected type: `inventory/localhost/` or `inventory/sample/`)
3. **Prompt for configuration values:**
   - Hugging Face Token (required for gated model downloads)
   - FQDN (Fully Qualified Domain Name, default: erag.com)
   - Kubernetes deployment choice (new cluster vs existing cluster)
   - Storage CSI driver (local-path-provisioner/nfs/netapp-trident)
   - Kubeconfig path (for existing clusters only - auto-set to `{config_dir}/artifacts/admin.conf` for new clusters)
   - Proxy settings (HTTP/HTTPS proxy configuration)

> **Note**: The `config.yaml` file is always sourced from `inventory/sample/` to maintain a single source of truth. Only the `inventory.ini` differs between localhost and sample deployments.

### Option 2: Manual Configuration

Create your configuration files manually:

1. **Copy sample configuration and choose inventory:**
   ```bash
   # For localhost deployment (existing Kubernetes cluster)
   mkdir -p /path/to/your/config-dir
   cp inventory/sample/config.yaml /path/to/your/config-dir/
   cp inventory/localhost/inventory.ini /path/to/your/config-dir/
   
   # OR for multi-node cluster deployment
   mkdir -p /path/to/your/config-dir
   cp inventory/sample/config.yaml /path/to/your/config-dir/
   cp inventory/sample/inventory.ini /path/to/your/config-dir/
   ```

2. **Edit configuration files:**
   ```bash
   # Edit main configuration
   vim /path/to/your/config-dir/config.yaml
   
   # Edit inventory for your hosts
   vim /path/to/your/config-dir/inventory.ini
   ```

### Environment Variables

The installer automatically loads environment variables from your shell session. These variables can be set before running deployment commands:

```bash
# Set default config directory (automatically used by installer)
export ERAG_CONFIG_DIR=/path/to/your/config-dir

# Set Hugging Face token (if not defined in config.yaml ENV will be used)
export HF_TOKEN=your_huggingface_token

# Set kubeconfig path (if not defined in config.yaml ENV will be used)
export KUBECONFIG=$HOME/.kube/config

# Note: When deploy_k8s=true, KUBECONFIG is automatically set to:
# {config_directory}/artifacts/admin.conf

# Set proxy settings (automatically suggested by installer)
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,10.0.0.0/8
```

**How Environment Variables Work:**

- `ERAG_CONFIG_DIR`: If set, the installer uses this as the default config directory instead of `inventory/cluster`
- `HF_TOKEN`: If config.yaml does not set huggingToken value env will be used.
- `KUBECONFIG`: If config.yaml does not set kubeconfig value env will be used.

## Validate Hardware Requirements

Before proceeding with deployment, validate your hardware meets the requirements:

```bash
./installer.sh validate hardware --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

> [!NOTE]
> For Gaudi deployments, ensure your `config.yaml` includes `is_gaudi_platform: true`

You can also validate just the configuration without hardware checks:

```bash
./installer.sh validate config --config=/path/to/config.yaml
```

### Inventory Requirements for Different Operations

The installer supports different inventory types depending on your deployment scenario. All deployments use the same `config.yaml` (from `inventory/sample/`), but differ in their `inventory.ini` file.

**Localhost Inventory (Application-Only Deployment)**

Use `inventory/localhost/inventory.ini` when:
- Deploying only the Enterprise RAG application on an existing Kubernetes cluster
- Your Kubernetes cluster is already set up and accessible via `KUBECONFIG`
- You're running the installer from a machine that can access the cluster

Example localhost inventory:
```ini
<hostname> ansible_connection=local ansible_python_interpreter=<repository_path>/deployment/erag-venv/bin/python3

[kube_control_plane]
<hostname>

[kube_node]
<hostname>

[k8s_cluster:children]
kube_control_plane
kube_node
```

**Sample Inventory (Multi-Node Cluster Deployment)**

Use `inventory/sample/inventory.ini` when:
- Deploying a new Kubernetes cluster across multiple nodes
- You have control plane and worker nodes to configure
- Setting up the complete infrastructure from scratch

Example sample inventory:
```ini
kube-master-1 ansible_host=<node1_ip_address>
kube-worker-1 ansible_host=<node2_ip_address>

[kube_control_plane]
kube-master-1

[kube_node]
kube-worker-1
```

**Configuration Files Structure:**

- `config.yaml`: Always use `inventory/sample/config.yaml` (single source of truth)
- `inventory.ini`: Choose between `inventory/localhost/inventory.ini` or `inventory/sample/inventory.ini`

**Operation Requirements:**

| Operation | Inventory Type | Notes |
|-----------|---------------|-------|
| `cluster deploy` | Localhost or Sample  | Requires all cluster nodes defined |
| `cluster delete` | Localhost or Sample  | Must match deployment inventory |
| `application install` | Localhost or Sample | Both work; localhost for existing clusters |
| `application uninstall` | Localhost or Sample | Match what was used for install |
| `stack deploy-complete` | Localhost or Sample | Choose based on cluster setup needs |

## Complete Stack Deployment (Recommended)

> **⚠️ Before Starting**: Ensure the virtual environment is activated:
> ```bash
> source erag-venv/bin/activate
> ```

Deploy the entire Enterprise RAG stack with a single command:

```bash
./installer.sh stack deploy-complete \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini
```

This comprehensive deployment includes:
- **System dependencies and tools configuration**
- **Kubernetes cluster deployment** (if configured)
- **Infrastructure components installation**
- **Enterprise RAG application deployment**

The complete stack deployment will:
1. Configure the system and install required tools
2. Deploy Kubernetes cluster (if `deploy_k8s: true` in config)
3. Deploy the Enterprise RAG application stack

> [!TIP]
> Use environment variables to simplify commands:
> ```bash
> export ERAG_CONFIG_DIR=/path/to/your/config-dir
> ./installer.sh stack deploy-complete
> ```

## Manual Step-by-Step Deployment

For advanced users who prefer granular control:

### 1. System Configuration

Configure the deployment environment and install required tools:

```bash
./installer.sh setup configure --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

### 2. Container Images (Optional)

Build and push custom container images:

```bash
./installer.sh setup images --tag=custom_build --registry=your-registry.com
```

### 3. Kubernetes Cluster Deployment

Deploy a new Kubernetes cluster:

```bash
./installer.sh cluster deploy --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

Perform post-installation tasks:

```bash
./installer.sh cluster post-install --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

### 4. Application Deployment

Deploy the Enterprise RAG application:

```bash
./installer.sh application install --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

Check deployment status and configuration:

```bash
./installer.sh application show-config --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
```

> [!TIP]
> Use environment variables to simplify commands:
> ```bash
> export ERAG_CONFIG_DIR=/path/to/your/config-dir
> ./installer.sh <command> <action>
> ```

## Update Application Components

After the application is installed, you can update components (models, configurations) by editing your configuration file and rerunning the install:

1. **Edit your configuration:**
   ```bash
   vim /path/to/config.yaml
   # Modify settings like llm_model, embedding_model_name, etc.
   ```

2. **Apply the changes:**
   ```bash
   ./installer.sh application install --config=/path/to/config.yaml --inventory=/path/to/inventory.ini
   ```

The deployment scripts will detect changes and update only the affected components, minimizing downtime.

## Create and Restore Backups

The application supports comprehensive backup and restore functionality for user data, configurations, and chat history.

For detailed instructions on backup configuration and operations, refer to the [Backup and Restore Guide](../docs/backup.md).

# Interact with ChatQnA

## Test Deployment

Verify that the deployment was successful:

```bash
./scripts/test_connection.sh
```

Expected output for a successful deployment:
```
deployment.apps/client-test created
Waiting for all pods to be running and ready....All pods in the chatqa namespace are running and ready.
Connecting to the server through the pod client-test-87d6c7d7b-45vpb using URL http://router-service.chatqa.svc.cluster.local:8080...
data: '\n'
data: 'A'
data: ':'
data: ' AV'
data: 'X'
data: [DONE]
Test finished successfully
```

## Access the UI/Grafana

### Port Forwarding Setup

1. **Forward the ingress port:**
   ```bash
   sudo -E kubectl port-forward --namespace ingress-nginx svc/ingress-nginx-controller 443:https
   ```

2. **Access from another machine (optional):**
   ```bash
   ssh -L 443:localhost:443 user@cluster-host-ip
   ```

3. **Update `/etc/hosts` file:**
   
   Add the following entries to your `/etc/hosts` file:
   ```
   127.0.0.1 erag.com grafana.erag.com auth.erag.com s3.erag.com minio.erag.com
   ```
   
   > [!NOTE]
   > On Windows, this file is located at `C:\Windows\System32\drivers\etc\hosts`

### Access URLs

Once configured, access the services via:

- **Enterprise RAG UI**: `https://erag.com`
- **Keycloak (Authentication)**: `https://auth.erag.com`
- **Grafana (Monitoring)**: `https://grafana.erag.com`
- **MinIO Console**: `https://minio.erag.com`
- **S3 API**: `https://s3.erag.com`

> [!CAUTION]
> If using self-signed certificates (default configuration), visit `https://s3.erag.com` in your browser and accept the certificate warning before data ingestion. This step is not required with custom SSL certificates.

## UI Credentials for the First Login

After deployment, find initial credentials in:
```
deployment/ansible-logs/default_credentials.txt
```

This file contains one-time passwords for:
- **Application Admin**: Full administrative access
- **Application User**: Standard user access

> [!IMPORTANT]
> - Change default passwords after first login
> - Remove the `default_credentials.txt` file after setup
> - Users will be prompted to change passwords on first login

## Credentials for Grafana and Keycloak

**Default Administrator Access:**
- **Username**: `admin`
- **Password**: Located in `ansible-logs/default_credentials.yaml`

> [!CAUTION]
> Secure the credentials file after first login:
> ```bash
> ansible-vault encrypt ansible-logs/default_credentials.yaml
> ```
> After encryption, add `--ask-vault-pass` to installer commands when needed.

## Credentials for Vector Store

Vector store credentials are automatically generated and stored in:
```
ansible-logs/default_credentials.yaml
```

## Credentials for Enhanced Dataprep Pipeline (EDP)

**MinIO Object Storage:**
- Use `erag-admin` user credentials for API and Web UI access

**Internal EDP Services:**

- **Redis**:
  - Username: `default`
  - Password: In `ansible-logs/default_credentials.yaml`

- **PostgreSQL**:
  - Username: `edp`
  - Password: In `ansible-logs/default_credentials.yaml`

## Data Ingestion, UI and Telemetry

- **UI Features and Data Ingestion**: [UI Features Guide](../docs/UI_features.md)
- **Monitoring and Telemetry**: [Telemetry Guide](../docs/telemetry.md)

## Configure Single Sign-On Integration Using Microsoft Entra ID

For enterprise SSO integration: [Single Sign-On Configuration Guide](../docs/single_sign_on_configuration_on_keyclock.md)

# Remove the Installation

## Complete Stack Removal

Remove the entire Enterprise RAG deployment:

```bash
./installer.sh stack delete-complete \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini
```

> [!WARNING]
> This operation is **DESTRUCTIVE** and **IRREVERSIBLE**. It will permanently delete:
> - All Enterprise RAG applications and data
> - Monitoring and observability stack
> - Kubernetes cluster (if deployed by this tool)
> - All persistent volumes and data
> - Configuration directories

## Application-Only Removal

Remove just the Enterprise RAG application (keeping the Kubernetes cluster):

```bash
./installer.sh application uninstall \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini
```

## Cluster-Only Removal

Remove just the Kubernetes cluster:

```bash
./installer.sh cluster delete \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini
```

---

## Advanced Usage

### Custom Tags and Registries

```bash
# Use custom image tags
./installer.sh application install \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini \
  --tag=v2.0.0

# Use custom registry
./installer.sh setup images \
  --registry=company-registry.com/erag \
  --tag=production
```

### Verbose Logging

Enable detailed Ansible output for troubleshooting:

```bash
./installer.sh application install \
  --config=/path/to/config.yaml \
  --inventory=/path/to/inventory.ini \
  -vvv
```

### Non-Interactive Configuration

Skip interactive prompts and use defaults:

```bash
./installer.sh setup config /path/to/new-config-directory \
  --non-interactive
```

### Environment Variable Configuration

```bash
# Set config directory globally
export ERAG_CONFIG_DIR=/opt/erag/configs

# Use simplified commands
./installer.sh validate hardware
./installer.sh stack deploy-complete
./installer.sh application show-config
```

---

## Troubleshooting

### Common Issues

1. **Failed to import the required Python library (kubernetes)**: You forgot to activate the virtual environment! Run `source erag-venv/bin/activate` first
2. **Permission Denied**: Ensure passwordless sudo is configured
3. **Python Virtual Environment**: Run `./installer.sh setup python-env` first
4. **Configuration Missing**: Verify config.yaml and inventory.ini exist
5. **Network Issues**: Check proxy settings in environment variables

### Python Environment Issues

**Problem**: `Failed to import the required Python library (kubernetes)` or similar import errors

**Root Cause**: Ansible is using the system Python instead of the virtual environment Python

**Solution**: Always activate the virtual environment before running any installer commands:

```bash
# Activate the virtual environment
source erag-venv/bin/activate

# For localhost-only deployments, set the Python interpreter
export ANSIBLE_PYTHON_INTERPRETER=$(pwd)/erag-venv/bin/python

# Verify Ansible is using the correct Python
ansible --version
which ansible
```

**Why this happens**: The virtual environment contains all required Python packages (kubernetes, etc.), but without activation, Ansible uses the system Python which typically lacks these dependencies. The error message `on igk-0940.igk.intel.com's Python /usr/bin/python3` shows it's using system Python instead of the venv Python.

**Note**: The installer will automatically detect and use the virtual environment's ansible-playbook if available, but manual activation ensures consistent Python package access.

### Getting Help

```bash
# Show detailed help
./installer.sh --help

# Show component-specific help
./installer.sh setup --help
```

### Log Files

Check deployment logs in:
```
ansible-logs/
```

---

*For additional documentation and advanced configuration options, refer to the [docs](../docs/) directory.*