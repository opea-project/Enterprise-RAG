# Solution Upgrade Guide

This document provides instructions for upgrading Intel&reg; AI for Enterprise RAG from one version to another.

## Table of Contents

1. [Introduction](#introduction)
1. [Prerequisites](#prerequisites)
1. [Upgrade Process](#upgrade-process)
1. [Verification](#verification)
1. [Rollback Procedure](#rollback-procedure)

## Introduction

The upgrade workflow uses a two-phase approach:

- **Phase 1**: Pre-upgrade assessment from your current deployment
- **Phase 2**: Upgrade execution from the target deployment

This ensures validation checks are performed before making changes to your running system.

## Prerequisites

### Backup Configuration

> [!IMPORTANT]
> A recent backup is required before upgrading. The upgrade workflow verifies backup availability.

Velero must be installed and configured. See the [Backup and Restore Guide](backup.md) for setup instructions.

Ensure your `config.yaml` has Velero enabled:
```yaml
velero:
  enabled: true
  namespace: velero
  install_server: true
  install_client: true
```

### Target Deployment

- Extract the target version package
- Copy your current `config.yaml` to the target deployment inventory folder
- Review and update any version-specific configuration changes

### Access Requirements

- Same `KUBECONFIG` environment variable for both deployments
- Permissions to deploy and manage cluster resources

## Upgrade Process

### Step 1: Create Backup

Before upgrading, create a backup of your current deployment:

```bash
cd deployment

ansible-playbook playbooks/backup.yaml --tags backup,monitor_backup \
  -e @inventory/test-cluster/config.yaml
```

Wait for completion and verify:

```bash
kubectl get backups -n velero
```

### Step 2: Prepare Target Deployment

Extract and prepare the new version:

```bash
# Extract target version
tar -xzf erag-2.1.0.tar.gz

# Copy configuration to target
# The config can be placed in any of these locations:
#   - deployment/inventory/<cluster>/config.yaml (recommended)
#   - deployment/config.yaml
cp deployment/inventory/test-cluster/config.yaml \
  ../erag-2.1.0/deployment/inventory/test-cluster/config.yaml
```

### Step 3: Run Pre-upgrade Assessment (Phase 1)

From your **current deployment**, run the pre-upgrade assessment:

```bash
cd deployment

ansible-playbook playbooks/pre_upgrade.yaml \
  -e target_config_path=/path/to/erag-2.1.0/deployment/inventory/test-cluster/config.yaml \
  -e @inventory/test-cluster/config.yaml
```

> **Note**: The playbook will automatically resolve the target deployment directory from the config path. The config can be located at `inventory/<cluster>/config.yaml`, or directly at `deployment/config.yaml`.

The assessment will:
- Check version compatibility (blocks downgrades)
- Verify backup availability
- Check system health

Review the output. The assessment indicates:
- **READY**: All checks passed, proceed with upgrade
- **WARNINGS**: Issues detected, review before proceeding

#### Optional: Detailed Pre-upgrade Checks

For comprehensive pre-upgrade validation including data consistency checks and metadata comparison, run from your **target deployment**:

```bash
cd deployment

ansible-playbook playbooks/application.yaml --tags pre-upgrade \
  -e @inventory/test-cluster/config.yaml
```

This performs:
- All Phase 1 checks (health, backup, version)
- Data consistency verification (EDP, VDB, SeaweedFS)
- Metadata comparison between current and target versions

### Step 4: Execute Upgrade (Phase 2)

If Phase 1 completed successfully, run the upgrade from the **target deployment**:

```bash
cd /path/to/erag-2.1.0/deployment

ansible-playbook playbooks/application.yaml --tags install \
  -e @inventory/test-cluster/config.yaml
```

## Verification

After upgrade completion, verify the deployment:

```bash
cd deployment
./scripts/query_deployment_manifest.sh
```

The output shows the deployed version and component status.

Test application functionality:
1. Access the UI and verify login
2. Test document ingestion
3. Verify chat functionality
4. Check existing data is accessible

## Rollback Procedure

If issues occur after upgrade:

### Step 1: Uninstall Target Deployment

```bash
cd /path/to/erag-2.1.0/deployment

ansible-playbook playbooks/application.yaml --tags uninstall \
  -e @inventory/test-cluster/config.yaml
```

### Step 2: Reinstall Source Deployment

```bash
cd /path/to/erag-2.0.1/deployment

ansible-playbook playbooks/application.yaml --tags install \
  -e @inventory/test-cluster/config.yaml
```

### Step 3: Restore from Backup

```bash
cd /path/to/erag-2.0.1/deployment

ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore \
  -e @inventory/test-cluster/config.yaml \
  -e '{"velero": {"restore_from": "backup-20260204t143000"}}'
```

Replace the backup name with the actual backup created in Step 1.
