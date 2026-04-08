# Velero Backup Storage Configuration

This document is intended for operators deploying Intel® AI for Enterprise RAG who need to choose and configure the backup storage backend for Velero.

## Table of Contents

1. [Overview](#overview)
1. [Local Storage (Default)](#local-storage-default)
1. [External Storage](#external-storage)
1. [Choosing Between Modes](#choosing-between-modes)
1. [Configuring External Storage](#configuring-external-storage)
   - [Credentials File](#credentials-file)
   - [TLS Configuration](#tls-configuration)
   - [Hostname Resolution](#hostname-resolution)
   - [AWS S3](#aws-s3)
   - [Evaluation: External SeaweedFS](#evaluation-external-seaweedfs)
   - [Verifying External BSL](#verifying-external-bsl)
1. [Network Considerations](#network-considerations)

## Overview

Velero requires a **Backup Storage Location (BSL)** — an S3-compatible object store — to persist backup metadata and volume-snapshot data. Intel® AI for Enterprise RAG supports two storage modes:

| Mode | BSL location | Deployment |
|------|-------------|------------|
| **Local** | In-cluster SeaweedFS instance | Deployed automatically with Velero |
| **External** | Any S3-compatible service outside the cluster | Operator-provisioned; in-cluster SeaweedFS is not deployed |

## Local Storage (Default)

When `external_bsl.enabled` is absent or `false`, Velero is configured to use an **in-cluster SeaweedFS instance** as its BSL. The SeaweedFS deployment is managed automatically by the same Ansible role that installs Velero.

**No extra configuration is required beyond enabling Velero:**

```yaml
# config.yaml
velero:
  enabled: true
```

**Characteristics:**

- Self-contained — no external dependencies or credentials to manage.
- Data is stored inside the cluster on the same storage backend as application workloads.
- Suitable for evaluating the backup feature or for single-cluster environments where losing the cluster also means accepting loss of backups.
- **Not suitable for disaster recovery** — if the cluster storage is lost, so are the backups.

## External Storage

When `external_bsl.enabled: true` is set, the **in-cluster SeaweedFS is not deployed**. Velero connects to the S3-compatible service specified by `s3_url` instead.

Any service supported by [velero-plugin-for-aws](https://github.com/vmware-tanzu/velero-plugin-for-aws) can be used: AWS S3, MinIO, Ceph RadosGW, NetApp StorageGRID, or other self-hosted S3 backends.

**Characteristics:**

- Backup data lives outside the cluster — cluster failure does not affect backup availability.
- Enables cross-cluster restore (from one cluster to another using the same BSL).
- Requires an independently operated S3 service with credentials management.
- Supports TLS and custom CA certificates.
- Required for any real disaster-recovery scenario.

## Choosing Between Modes

| Criterion | Local | External |
|-----------|-------|----------|
| Setup effort | Minimal | Requires an S3 service |
| Backup survives cluster loss | No | Yes |
| Cross-cluster restore | No | Yes |
| Credential management | None | Yes (AWS INI file) |
| Suitable for production DR | No | Yes |

## Configuring External Storage

Set `external_bsl.enabled: true` and provide the endpoint and credentials in `config.yaml`:

```yaml
velero:
  external_bsl:
    enabled: true
    s3_url: "https://my-s3.example.com:9000"
    bucket: "velero-backups"
    credentials_file_path: "/path/to/credentials"
    region: "us-east-1"
    s3_force_path_style: "true"   # true for self-hosted S3; false for AWS S3
    tls:
      enabled: false
```

### Credentials File

Create an AWS INI–format credentials file:

```ini
[default]
aws_access_key_id = <ACCESS_KEY>
aws_secret_access_key = <SECRET_KEY>
```

Set `credentials_file_path` to its absolute path. The Ansible role reads this file, creates a Kubernetes Secret, and mounts it into the Velero pod. `credentials_file_path` and `credentials_secret` are mutually exclusive — use the former when you want Ansible to manage the Secret.

### TLS Configuration

If the S3 endpoint uses TLS with a custom CA:

```yaml
    tls:
      enabled: true
      ca_cert_path: "/path/to/ca.crt"   # PEM-encoded CA certificate
      hostname: "my-s3.example.com"
```

The Ansible role creates a ConfigMap from the CA certificate, mounts it into the Velero pod, and sets `caCert` on the BSL so that Velero validates the certificate.

### Hostname Resolution

If cluster nodes cannot resolve the BSL hostname through standard DNS, set `host_ip` to inject a `hostAliases` entry into the Velero pod:

```yaml
    tls:
      enabled: true
      hostname: "my-s3.example.com"
      host_ip: "10.0.0.50"
```

This does not modify `/etc/hosts` on nodes; it only affects the Velero pod. For cluster-wide resolution, patch CoreDNS instead — see the external-seaweedfs README for an example.

### AWS S3

AWS S3 requires a few settings that differ from self-hosted S3 backends:

```yaml
velero:
  external_bsl:
    enabled: true
    # Do NOT set s3_url — omitting it tells the plugin to use the
    # default regional AWS endpoint (s3.<region>.amazonaws.com).
    bucket: "my-velero-bucket"
    credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/aws-s3-credentials"
    region: "us-west-2"          # must match the bucket's region
    s3_force_path_style: "false"  # AWS deprecated path-style; virtual-hosted style is required
    checksumAlgorithm: ""         # disable CRC64 default added in recent AWS SDK — required for velero-plugin-for-aws v1.12.x
    tls:
      enabled: false              # AWS S3 uses public TLS — no custom CA needed
```

> **`s3_url` must be absent or empty for real AWS.** Setting it to an AWS endpoint URL is valid, but omitting it is simpler and more reliable — the plugin automatically constructs the correct regional endpoint from `region`.

> **`checksumAlgorithm: ""`** is required to suppress the CRC64 checksum default introduced in recent AWS SDK versions, which conflicts with how `velero-plugin-for-aws` v1.12.x handles multipart uploads. Without this, DataUploads may fail.

**IAM permissions** — the credentials user needs only bucket-scoped S3 operations. The minimal inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:PutObjectTagging",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-velero-bucket",
        "arn:aws:s3:::my-velero-bucket/*"
      ]
    }
  ]
}
```

Deliberately exclude `s3:DeleteBucket` so the user cannot accidentally remove the bucket.

**S3 bucket settings** — enable versioning and server-side encryption (SSE-S3) at bucket creation:

```bash
aws s3api create-bucket --bucket my-velero-bucket --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2
aws s3api put-bucket-versioning --bucket my-velero-bucket \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket my-velero-bucket \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

**Proxy** — in environments with a corporate HTTP proxy, AWS S3 traffic must flow through the proxy. The Ansible role sets `HTTPS_PROXY` in the Velero pod environment automatically. Do **not** add `*.amazonaws.com` to `NO_PROXY` — doing so bypasses the proxy and breaks connectivity in restricted networks.

After applying this configuration, reinstall Velero with the post-delete and post-install infrastructure tags:

```bash
ansible-playbook playbooks/infrastructure.yaml -t post-delete \
  -i inventory/cluster-<SUFFIX>/inventory.ini \
  -e @inventory/cluster-<SUFFIX>/config.yaml

ansible-playbook playbooks/infrastructure.yaml -t post-install \
  -i inventory/cluster-<SUFFIX>/inventory.ini \
  -e @inventory/cluster-<SUFFIX>/config.yaml
```

If the post-install run reports a single failure on the "Discover velero version" task (`failed CONNECT via proxy status: 403`), this is a non-critical cosmetic failure — the Velero deployment and BSL configuration succeed regardless. The task attempts `kubectl exec` into the distroless Velero pod through the proxy; verify the deployment directly:

```bash
kubectl -n velero get backupstoragelocation
# Expected: default   aws   <bucket>   Available
```

### Evaluation: External SeaweedFS

`deployment/components/external-seaweedfs/` provides a Docker Compose–based SeaweedFS service and a helper script (`setup.sh`) for quickly standing up an off-cluster S3 endpoint on the Ansible controller host. This is intended for evaluating external BSL configuration without requiring a full S3 service.

```bash
# TLS + hostname (recommended for realistic evaluation)
./setup.sh --install --hostname HOSTNAME [--host HOST_IP]

# Plain HTTP (IP-only)
./setup.sh --install [--host HOST_IP]
```

After running `setup.sh`, paste the printed `external_bsl` config snippet into `config.yaml`, then apply:

```bash
ansible-playbook playbooks/infrastructure.yaml -t post-install \
  -e @inventory/test-cluster/config.yaml
```

See [deployment/components/external-seaweedfs/README.md](../deployment/components/external-seaweedfs/README.md) for full setup and management instructions.

### Verifying External BSL

After the `post-install` step completes, the Ansible role automatically checks that the BSL reports `Available`. If it does not reach `Available` within ~3 minutes, the play fails with guidance on what to inspect.

To verify manually at any time:

```bash
kubectl -n velero get backupstoragelocation
```

Expected output:

```
NAME      PHASE       LAST VALIDATED   AGE
default   Available   ...              ...
```

If the phase is `Unavailable` or the field is empty, check the Velero pod logs:

```bash
kubectl -n velero logs deployment/velero | grep -i 'backupstoragelocation\|error\|fail'
```

Common causes:

| Symptom | Likely cause |
|---------|--------------|
| `connection refused` / timeout | S3 endpoint unreachable; check `s3_url`, firewall, and proxy |
| `SignatureDoesNotMatch` | Wrong `aws_secret_access_key` |
| `NoSuchBucket` | Bucket does not exist or `bucket` field typo |
| `InvalidBucketName` | AWS path-style used; set `s3_force_path_style: "false"` |
| TLS handshake errors | Wrong or missing CA cert; check `tls.ca_cert_path` |
| `RequestError` / `no such host` | Hostname not resolvable; see [Hostname Resolution](#hostname-resolution) |

## PV Data Mover Configuration

Velero's **node-agent** and **data mover** enable file-level backup of persistent volumes without requiring CSI snapshots. This is particularly useful for cross-cluster restore scenarios or when backing up to external storage.

**Auto-configuration:** By default (when set to `"auto"`), both features are enabled when `external_bsl.enabled: true` and disabled when using local storage. This matches the typical use case where external storage is used for disaster recovery with full PV backups.

**Override when needed:** Set `enabled: true` or `enabled: false` in `config.yaml` to override:

```yaml
velero:
  node_agent:
    enabled: true    # Force enable even with local storage (for testing)
  data_mover:
    enabled: false   # Disable even with external storage (to save space)
  external_bsl:
    enabled: true
```

## Network Considerations

When using an external BSL, both the Velero pod (running in the cluster) and the `velero` CLI (running on the Ansible controller) need direct access to the BSL endpoint. In environments with an HTTP proxy, this requires explicit configuration.

**Velero pod:** The Ansible role automatically adds the BSL endpoint hostname and IP to `NO_PROXY` in the Velero pod's environment. No manual action is needed.

**Velero CLI on the controller:** After the post-install step, Ansible generates a shell snippet at `deployment/ansible-logs/velero-env.sh` that configures the same settings for interactive use:

```bash
source deployment/ansible-logs/velero-env.sh
velero backup get
velero backup describe <BACKUP_NAME> --details
velero restore describe <RESTORE_NAME>
```

The snippet sets:

- `no_proxy` / `NO_PROXY` — adds the BSL hostname and IP to bypass the corporate proxy.
- `SSL_CERT_FILE` — points to the CA certificate so the CLI trusts the BSL TLS certificate (TLS mode only).

Without sourcing this snippet, CLI commands that retrieve detailed data directly from the BSL (such as `backup describe --details`) will fail with proxy timeout or TLS errors.

For usage in the context of backup and restore operations, see [docs/backup.md](backup.md#external-backup-storage).
