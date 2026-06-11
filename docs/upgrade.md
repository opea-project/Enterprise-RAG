# Solution Upgrade Guide

This document provides instructions for upgrading Intel&reg; AI for Enterprise RAG from one version to another.

## Table of Contents

1. [Introduction](#introduction)
1. [Prerequisites](#prerequisites)
1. [Upgrade Process](#upgrade-process)
1. [Verification](#verification)
1. [Rollback Procedure](#rollback-procedure)
1. [Version-specific Notes](#version-specific-notes)

## Introduction

The upgrade workflow is supported by standard install flow, which auto-detects upgrades by comparing the deployed version (stored in a Kubernetes ConfigMap) against the target version. When an upgrade is detected, the install automatically performs version constraint validation, health checks, data consistency verification, and generates reports.

Running a pre-upgrade assessment beforehand is recommended but not required — it lets you review compatibility and system health before making changes.

## Prerequisites

### Backup Configuration

> [!IMPORTANT]
> Creating a backup before upgrading is strongly recommended. By default, the upgrade workflow verifies that a recent backup exists and will block if none is found.

If you use Velero for backups, ensure it is installed and configured. See the [Backup and Restore Guide](backup.md) for setup instructions.

Ensure your `config.yaml` has Velero enabled:
```yaml
velero:
  enabled: true
  namespace: velero
  install_server: true
  install_client: true
```

If you manage backups through a different mechanism or want to skip the backup check, pass `-e allow_upgrade_without_backup=true` when running the pre-upgrade assessment and/or install. This bypasses backup verification in both playbooks.

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
tar -xzf erag-2.3.0.tar.gz

# Copy configuration to target
# The config can be placed in any of these locations:
#   - deployment/inventory/<cluster>/config.yaml (recommended)
#   - deployment/config.yaml
cp deployment/inventory/test-cluster/config.yaml \
  ../erag-2.3.0/deployment/inventory/test-cluster/config.yaml
```

> [!IMPORTANT]
> After copying, update the `tag` field in the target `config.yaml` to match the version of ERAG solution indicated in `deployment/version.yaml`:
> ```yaml
> tag: <deployment_target_version>
> ```
> This controls which container images are deployed. If the image registry has also changed, update the `registry` field as well.

### Step 3: Run Pre-upgrade Assessment (Recommended)

From your **current deployment**, run the pre-upgrade assessment:

```bash
cd deployment

ansible-playbook playbooks/pre_upgrade.yaml \
  -e target_config_path=/path/to/erag-2.3.0/deployment/inventory/test-cluster/config.yaml \
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

For a more comprehensive check that also includes data consistency verification and metadata comparison between current and target versions, run `ansible-playbook playbooks/application.yaml --tags pre-upgrade` from the **target deployment** instead.

### Step 4: Execute Upgrade

Run the install from the **target deployment**:

```bash
cd /path/to/erag-2.3.0/deployment

ansible-playbook playbooks/application.yaml --tags install \
  -e @inventory/test-cluster/config.yaml
```

The install flow auto-detects that this is an upgrade and automatically performs:
- Version constraint validation (blocks unsupported upgrade paths)
- Pre and post health checks with comparison
- Data consistency verification (EDP, VDB, SeaweedFS)
- Report generation under `deployment/upgrade/reports/`

## Verification

After upgrade completion, review the auto-generated upgrade summary:

```bash
cat deployment/upgrade/reports/upgrade-summary.md
```

This report covers upgrade mode, health check results, and data consistency status.

Verify the deployed version:

```bash
cd deployment
./scripts/query_deployment_manifest.sh
```

Test application functionality:
1. Access the UI and verify login
2. Test document ingestion
3. Verify chat functionality
4. Check existing data is accessible

### Post-Upgrade Re-embedding (If Embedding Model Changed)

If you switched to a new embedding model during the upgrade, all existing documents need to be embedded again.

Go to Admin Panel → Data Ingestion. If any documents require re‑ingestion, you’ll see a warning banner there automatically. The system keeps track of which embedding model was used for each file, so any documents embedded with the previous model will be flagged until they’re reingested. Once all documents are re‑ingested with the new model, the warning banner will disappear automatically.

#### Automating the Embedding Model Decision in CI/CD

During the pre-upgrade assessment, when an embedding model change is detected the playbook normally pauses and waits for operator input. To skip the interactive prompt in automated pipelines, pass `embedding_model_decision_action`:

```bash
# Accept the new model — migration ConfigMap is created, re-embedding banner will appear after upgrade
ansible-playbook playbooks/application.yaml --tags pre-upgrade \
  -e @inventory/test-cluster/config.yaml \
  -e embedding_model_decision_action=use_new_model

# Keep the previous model — playbook exits with instructions to update config.yaml
ansible-playbook playbooks/application.yaml --tags pre-upgrade \
  -e @inventory/test-cluster/config.yaml \
  -e embedding_model_decision_action=keep
```

Accepted values are `use_new_model` and `keep`. Any other value fails immediately with a validation error. When the variable is not set, the interactive prompt is always shown regardless of environment — the override has no effect on runs where no embedding model change is detected.


## Rollback Procedure

If issues occur after upgrade:

### Step 1: Uninstall Target Deployment

```bash
cd /path/to/erag-2.3.0/deployment

ansible-playbook playbooks/application.yaml --tags uninstall \
  -e @inventory/test-cluster/config.yaml
```

### Step 2: Reinstall Source Deployment

```bash
cd /path/to/erag-2.2.0/deployment

ansible-playbook playbooks/application.yaml --tags install \
  -e @inventory/test-cluster/config.yaml
```

### Step 3: Restore from Backup

```bash
cd /path/to/erag-2.2.0/deployment

ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore \
  -e @inventory/test-cluster/config.yaml \
  -e '{"velero": {"restore_from": "backup-20260204t143000"}}'
```

Replace the backup name with the actual backup created in Step 1.

## Version-specific Notes

This section collects upgrade considerations that apply only when crossing specific version boundaries. Add a new subsection here whenever a release introduces a breaking change, a mandatory manual step, or a new automation variable that operators need to know about.

### 2.2.0 — Default Embedding Model Change

The default embedding model changed from `BAAI/bge-base-en-v1.5` to `nomic-ai/nomic-embed-text-v1`.

Operators upgrading from any earlier version will encounter the embedding model decision prompt during pre-upgrade assessment (see [Automating the Embedding Model Decision in CI/CD](#automating-the-embedding-model-decision-in-cicd)). The two options are:

- **Keep `BAAI/bge-base-en-v1.5`**: set `embedding_model_name: "BAAI/bge-base-en-v1.5"` in your target `config.yaml` before running pre-upgrade. No re-embedding required.
- **Switch to `nomic-ai/nomic-embed-text-v1`**: proceed without changing `config.yaml`. All existing documents must be re-embedded after upgrade via Admin Panel → Data Ingestion.
