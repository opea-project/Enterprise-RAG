# Enterprise RAG Debug Tool

Collects comprehensive diagnostic information from a Kubernetes cluster including pod logs, resource descriptions, and deployment configuration (with sensitive data redacted).

## Setup

### Using existing virtual environment

The debug tool requires Python dependencies to run. During the initial deployment, a virtual environment was created at `../erag-venv/`. You can reuse this environment:

```bash
source ../erag-venv/bin/activate
```

If the virtual environment was deleted or is no longer available, you can recreate it following the instructions below.

### Creating a new virtual environment

If the virtual environment doesn't exist or needs to be recreated:

```bash
cd deployment/
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install -r requirements.txt
```

After running these commands, the virtual environment will be ready to use for future runs.

## Usage

```bash
python tools/debug_tool.py [--output-dir <dir>] [--config /path/to/config.yaml]
```

### Parameters

- `--output-dir` (optional): Output directory for debug bundle. Defaults to `debug_bundle`. A timestamp is appended to create a unique directory.
- `--config` (optional): Path to the deployment configuration file (same file used during deployment). Must include the `kubeconfig` variable pointing to a valid kubeconfig file. The kubeconfig path can be absolute or relative to the config file location.

## Output Bundle Contents

- `kubectl_logs/`: Pod logs organized by namespace (current and previous)
- `kubectl_get/`: `kubectl get -o wide` output per resource type
- `kubectl_getyaml/`: `kubectl get -o yaml` output per resource type
- `kubectl_describe/`: `kubectl describe` output per resource type
- `topology_preview.txt`: Ansible topology preview output (if config provided)
- `config_redacted.yaml`: Deployment config with sensitive values redacted (if provided)
- `SUMMARY.json`: Quick overview of collected data
- `debug_tool_execution.log`: Complete log of debug tool execution

> **Note:** ConfigMaps and Secrets are only listed via `kubectl get` (no yaml/describe) to avoid exposing sensitive data.
> **Note:** If a deployment config is provided via `--config`, all sensitive fields (tokens, passwords, keys, etc.) are automatically redacted before saving.

## Common Troubleshooting Scenarios

### Pod Crash Loops
- Check `kubectl_logs/{namespace}/{pod}_previous.log` for crash details
- Review `kubectl_get/events.txt` for related events

### Performance Issues
- Check `kubectl_get/nodes.txt` and `kubectl_describe/nodes.txt` for node details
- Review logs for slow response times

### Storage Issues
- Check `kubectl_get/pvc.txt`, `kubectl_get/pv.txt` and `kubectl_get/sc.txt`
- Review `kubectl_getyaml/pvc.txt` for detailed PVC/PV configuration
- Look for storage-related events in `kubectl_get/events.txt`

### Network Connectivity
- Review `kubectl_get/networkpolicies.txt` and `kubectl_getyaml/networkpolicies.txt`
- Check `kubectl_get/services.txt` and `kubectl_get/ingress.txt`
- Look for network-related errors in pod logs
