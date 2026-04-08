# External SeaweedFS

## Motivation
`setup.sh` deploys a local [SeaweedFS](https://github.com/seaweedfs/seaweedfs) instance via Docker Compose
to serve as an off-cluster S3-compatible store for the Velero BSL — primarily for **evaluation** of external
backup storage. It is not intended as a production-ready backup solution.

The accompanying changes to the Velero role decouple backup storage from the cluster and support any
S3-compatible service. `setup.sh` is one quick-start option; for other stores (AWS S3, MinIO, Ceph RadosGW,
etc.) no local deployment is needed — see [Using a Different S3-Compatible Store](#using-a-different-s3-compatible-store).


## Implications for ERAG Solution
Implemented changes in Velero role allow decoupling backup storage from Velero deployment and the cluster deployment itself.
Once `external_bsl` is enabled and configured in `config.yaml`, the in-cluster storage will no longer be deployed.

Any S3-compatible storage service supported by `aws-plugin-for-velero` can be used as destination for
backup metadata and volume snapshots — see [Using a Different S3-Compatible Store](#using-a-different-s3-compatible-store)
for configuring stores other than the SeaweedFS instance deployed by `setup.sh`.

## Connection Modes

Two main modes are supported:

| Mode | S3 endpoint | TLS | Hostname resolution |
|------|-------------|-----|---------------------|
| **IP-only** | `http://HOST_IP:8333` | None | Not needed |
| **TLS + hostname** | `https://HOSTNAME:8333` | nginx terminator | Velero pod `hostAliases` (+ optional CoreDNS patch) |

## Architecture

**IP-only (plain HTTP):**
```
┌─ Host: HOST_IP ───────────────────────────────────────────┐
│  master :9333    volume :8080    filer (S3 HTTP :8333)     │
└────────────────────────────────────────────────────────────┘
```

**TLS + hostname (nginx terminates TLS):**
```
┌─ Host: HOSTNAME (HOST_IP) ────────────────────────────────┐
│  master :9333   volume :8080   filer :8444 ◄── nginx :8333│
└────────────────────────────────────────────────────────────┘
  Velero connects via https://HOSTNAME:8333
  (resolved inside the pod via hostAliases — no /etc/hosts on nodes)
```

> SeaweedFS native Go TLS has a TLS 1.3 HelloRetryRequest hang affecting
> OpenSSL-based clients. nginx terminates TLS cleanly as a workaround.

---

## Quick Start

```bash
# TLS + hostname
./setup.sh --install --hostname HOSTNAME [--host HOST_IP]

# Plain HTTP (IP-only)
./setup.sh --install [--host HOST_IP]

# Teardown
./setup.sh --uninstall --clean-volumes
```

After install, paste the printed config snippet into `config.yaml` (under `velero:`),
then apply:

```bash
ansible-playbook playbooks/infrastructure.yaml -t post-install \
  -e @inventory/test-cluster/config.yaml
```

### Commands & Options

| Command | Description |
|---------|-------------|
| `--install` | Deploy containers, generate credentials |
| `--uninstall` | Stop containers, remove generated files |
| `--patch-coredns` | Add `HOSTNAME→HOST_IP` to CoreDNS (needs `--hostname`, `kubectl`) |
| `--unpatch-coredns` | Remove `hosts` block from CoreDNS |

| Option | Used with | Description |
|--------|-----------|-------------|
| `--hostname <name>` | `--install` | Enable TLS (nginx + self-signed cert) |
| `--host <ip>` | `--install`, `--patch-coredns` | Server IP (default: auto-detected) |
| `--bucket <name>` | `--install` | S3 bucket name (default: `velero`) |
| `--port <port>` | `--install` | S3 port (default: `8333`) |
| `--local-volumes` | `--install` | Bind-mount data dirs instead of Docker volumes |
| `--base-path <dir>` | `--install` | Root for local volume dirs (default: `.`) |
| `--clean-volumes` | `--uninstall` | Also remove Docker volumes and local data dirs |

---

## Config Snippets

Below are given snippets of config to apply in Velero to enable external storage **instead of** deploying in-cluster storage:

**TLS + hostname:**
```yaml
    external_bsl:
      enabled: true
      s3_url: "https://HOSTNAME:8333"
      bucket: "velero"
      credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/cloud-credentials"
      region: "us-east-1"
      s3_force_path_style: "true"
      tls:
        enabled: true
        hostname: "HOSTNAME"
        host_ip: "HOST_IP"
        ca_cert_path: "{{ playbook_dir }}/../components/external-seaweedfs/certs/tls.crt"
```

**IP-only (plain HTTP):**
```yaml
    external_bsl:
      enabled: true
      s3_url: "http://HOST_IP:8333"
      bucket: "velero"
      credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/cloud-credentials"
      region: "us-east-1"
      s3_force_path_style: "true"
      tls:
        enabled: false
```

**Hostname without TLS** (requires separate DNS or CoreDNS patch):
```yaml
    external_bsl:
      enabled: true
      s3_url: "http://HOSTNAME:8333"
      bucket: "velero"
      credentials_file_path: "{{ playbook_dir }}/../components/external-seaweedfs/cloud-credentials"
      region: "us-east-1"
      s3_force_path_style: "true"
      tls:
        enabled: false
        host_ip: "HOST_IP"
```

### Extra BSL config (AWS plugin passthrough)

Any key in `external_bsl.config` is passed directly to the
[velero-plugin-for-aws BSL config](https://github.com/vmware-tanzu/velero-plugin-for-aws/blob/v1.12.1/backupstoragelocation.md):

```yaml
      config:
        checksumAlgorithm: ""
        insecureSkipTLSVerify: "true"
```

---

## What the Ansible Role Does

When `credentials_file_path` is set:
- Reads the AWS INI file and creates a K8s Secret (`velero-bsl-credentials`)
- Configures the Helm chart to reference that secret

When `ca_cert_path` is set (TLS mode):
- Creates a ConfigMap (`velero-bsl-ca-cert`) with the PEM cert
- Mounts it into the Velero pod, sets `caCert` on the BSL
- Injects `hostAliases` for hostname resolution

When `host_ip` is set (any mode):
- Injects `hostAliases` if the hostname differs from the IP
- Adds hostname + IP to `NO_PROXY` in the Velero pod

After install, a `velero-env.sh` snippet is generated in `ansible-logs/`.
Source it to configure `no_proxy` and `SSL_CERT_FILE` for ad-hoc velero CLI usage:
```bash
source deployment/ansible-logs/velero-env.sh
velero backup get
```

> `credentials_secret` and `credentials_file_path` are mutually exclusive.

---

## Using a Different S3-Compatible Store

`setup.sh` and the SeaweedFS containers are **not required** to use an external BSL. Any S3-compatible
service supported by [velero-plugin-for-aws](https://github.com/vmware-tanzu/velero-plugin-for-aws/blob/v1.12.1/backupstoragelocation.md)
can be configured directly — including AWS S3, MinIO, Ceph RadosGW, and others.

**Step 1.** Create a credentials file in AWS INI format:

```ini
[default]
aws_access_key_id = <ACCESS_KEY>
aws_secret_access_key = <SECRET_KEY>
```

**Step 2.** Configure `external_bsl` in `config.yaml` (example for AWS S3):

```yaml
velero:
  external_bsl:
    enabled: true
    s3_url: ""                          # leave empty for AWS S3 default endpoint
    bucket: "my-backup-bucket"
    credentials_file_path: "/path/to/credentials"
    region: "us-east-1"
    s3_force_path_style: "false"        # false for AWS S3; true for most self-hosted
    tls:
      enabled: false                    # set true + ca_cert_path for a custom CA
    config:
      checksumAlgorithm: ""            # any additional velero-plugin-for-aws BSL option
```

**Step 3.** Apply:

```bash
ansible-playbook playbooks/infrastructure.yaml -t post-install \
  -e @inventory/test-cluster/config.yaml
```

Full list of supported `config:` keys: [velero-plugin-for-aws BSL docs](https://github.com/vmware-tanzu/velero-plugin-for-aws/blob/v1.12.1/backupstoragelocation.md).

---

## Managing the Service

```bash
docker compose ps              # Status
docker compose logs -f         # All logs
docker compose logs -f filer   # Single service
docker compose restart         # Restart
docker compose down            # Stop (volumes preserved)
```

---

## CLI Access

```bash
# Read credentials
eval $(awk -F' = ' \
  '/aws_access_key_id/{print "export AWS_ACCESS_KEY_ID="$2}
   /aws_secret_access_key/{print "export AWS_SECRET_ACCESS_KEY="$2}' \
  cloud-credentials)
export AWS_EC2_METADATA_DISABLED=true

# TLS mode
alias aws-fs='no_proxy="*" NO_PROXY="*" aws --no-cli-pager \
  --endpoint-url https://HOSTNAME:8333 --ca-bundle certs/tls.crt'

# IP-only mode
alias aws-fs='no_proxy="*" NO_PROXY="*" aws --no-cli-pager \
  --endpoint-url http://HOST_IP:8333'

# Common commands
aws-fs s3 ls s3://velero/
aws-fs s3 ls s3://velero/ --recursive
aws-fs s3 rm s3://velero/ --recursive   # purge bucket
```

### Web UIs (plain HTTP, no auth)

- Master: `http://HOST_IP:9333/ui/index.html`
- Volume: `http://HOST_IP:8080/ui/index.html`
- Filer: `http://HOST_IP:8888/`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `SSL certificate verify failed` | Pass `--cacert certs/tls.crt` or `--no-verify-ssl` |
| `Failed to connect to proxy URL` | Add HOST_IP to `no_proxy` (use explicit IPs, not CIDRs) |
| BSL `Unavailable` after `post-install` | Paste `setup.sh` snippet into `config.yaml`, re-run `post-delete` + `post-install` |
| Backup stuck in `Finalizing` | Use `checksumAlgorithm: ""` in `external_bsl.config` |

---

## Generated Files

| File | Description |
|------|-------------|
| `cloud-credentials` | AWS INI credentials (referenced by `credentials_file_path`) |
| `s3config.json` | SeaweedFS S3 identity config |
| `docker-compose.override.yml` | Port/TLS/volume overrides (merged by Docker Compose) |
| `certs/tls.crt` | Self-signed cert *(TLS only)* |
| `certs/tls.key` | TLS private key *(TLS only)* |
| `certs/nginx.conf` | nginx config *(TLS only)* |

## Related Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Base container definitions |
| `roles/infrastructure/velero/tasks/main.yaml` | Velero Ansible tasks |
| `roles/infrastructure/velero/templates/values.yaml.j2` | Velero Helm values |
| `roles/infrastructure/velero/defaults/main.yaml` | Default config schema |
