# Intel® AI for Enterprise RAG - Usage Guide

## Prerequisites

- **Passwordless sudo:** Required for smooth deployment. Setup with:
  ```bash
  sudo visudo
  # Add line: %sudo ALL=(ALL) NOPASSWD:ALL
  ```
  Or for your user only:
  ```bash
  sudo visudo
  # Add line: username ALL=(ALL) NOPASSWD:ALL
  ```

- **Proxy Configuration (if behind corporate proxy):** When running from a machine behind a proxy, ensure that the Kubernetes control-plane IP is added to `no_proxy`/`NO_PROXY` to allow direct communication:
  ```bash
  export no_proxy="<control-plane-ip>,localhost,127.0.0.1,$no_proxy"
  export NO_PROXY="$no_proxy"
  ```
  This prevents the proxy from intercepting internal cluster traffic and causing connection failures.

## Quick Start

```bash
cd deployment/

# 1. Create Python virtual environment (installs Ansible + dependencies)
./installer.sh setup python-env

# 2. Activate the virtual environment
source erag-venv/bin/activate

# 3. Generate configuration interactively (config.yaml + inventory.ini)
./installer.sh setup config

# 4. Deploy the full stack
./installer.sh stack deploy
```

## Full Deployment Flow

### Step 1: Python Environment

```bash
./installer.sh setup python-env
```

Creates `erag-venv/` with Ansible and all required Python packages. You only need to do this once.

### Step 2: Activate the Environment

```bash
source erag-venv/bin/activate
```

**You must source the venv before running any other installer commands** (except `setup python-env` and `setup config`). For remote/multi-node inventories, Ansible will auto-discover the Python interpreter on target hosts. For localhost, it inherits from your active shell.

### Step 3: Generate Configuration

```bash
./installer.sh setup config                    # uses default directory
./installer.sh setup config /path/to/my-config # if custom directory is used used must provide --inventory --config flags to other commands
```

The interactive wizard asks you to choose:

| Option | Type | Description |
|--------|------|-------------|
| 1 | **localhost** | Deploy on an existing Kubernetes cluster (single node) |
| 2 | **remote** | Remote multi-node cluster deployment |

If you select **remote**, you **must edit the generated `inventory.ini`** before proceeding — fill in node hostnames, IP addresses, SSH user, and control plane/worker assignments.

The wizard also prompts for: HF token, FQDN, kubeconfig path, proxy settings, and whether to deploy a new K8s cluster.

### Step 4: Deploy

**Complete stack (recommended):**
```bash
./installer.sh stack deploy --config=<config-dir>/config.yaml --inventory=<config-dir>/inventory.ini
```

This runs configure → cluster deploy → application install in sequence.

**Step-by-step (manual control):**
```bash
./installer.sh setup configure    --config=<dir>/config.yaml
./installer.sh cluster deploy     --config=<dir>/config.yaml
./installer.sh application install --config=<dir>/config.yaml
```

## Command Reference

```
./installer.sh <component> <action> [options]
```

| Component | Action | Description |
|-----------|--------|-------------|
| `setup` | `python-env` | Create venv and install dependencies |
| `setup` | `config` | Interactive configuration generator |
| `setup` | `configure` | Install system dependencies (kubectl, helm) |
| `setup` | `images` | Build and push container images |
| `cluster` | `deploy` | Deploy Kubernetes cluster |
| `cluster` | `post-install` | Run post-install tasks |
| `cluster` | `delete` | Delete Kubernetes cluster |
| `application` | `install` | Install Enterprise RAG |
| `application` | `uninstall` | Uninstall Enterprise RAG |
| `application` | `show-config` | Show current config status |
| `stack` | `deploy` | Full deployment (configure + cluster + app) |
| `stack` | `delete` | Full teardown |

## Options

| Flag | Description |
|------|-------------|
| `--config=<path>` | Path to `config.yaml` |
| `--inventory=<path>` | Path to `inventory.ini` |
| `--tag=<tag>` | Override image tag |
| `--registry=<url>` | Override image registry |
| `--non-interactive` | Use defaults, skip prompts |
| `-v` / `-vv` / `-vvv` | Ansible verbosity |

When `--config` and `--inventory` are not specified, defaults are loaded from `inventory/cluster/`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | Hugging Face token for gated model downloads |

## Teardown

```bash
./installer.sh stack delete --config=<config-dir>/config.yaml
```

Removes the application, Kubernetes cluster, and optionally the config directory. Requires typing `DELETE` to confirm.

## Known Issues

### Localhost deployments require `ansible_python_interpreter` for post-install steps

When deploying on **localhost**, some Ansible tasks (e.g. post-install) require Python libraries installed in the venv (such as `kubernetes`). By default, Ansible on localhost uses the system Python, which doesn't have these libraries.

To fix this, set `ansible_python_interpreter` in your localhost inventory to point to the venv Python:

```ini
localhost ansible_connection=local ansible_python_interpreter=<repository_path>/deployment/erag-venv/bin/python3
```

This ensures Ansible uses the venv where all required pip packages are installed. Remote/multi-node inventories are not affected — they auto-discover the Python interpreter on target hosts.
