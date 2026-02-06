# NRI Balloons Controller

A Kubernetes webhook that mutates pods containing a specific container name (configured via ConfigMap) to add init containers, which waits for NRI balloons Daemonset to be ready.

## How It Works

The controller uses a mutating webhook to intercept Pod creation:
1. When a pod is created, the webhook checks if it contains a container with the name specified in the ConfigMap
2. If it does and the pod doesn't already have the init container, the webhook adds it to the pod spec
3. If needed, it also adds service account for init container
4. The modified pod is then created in the cluster with the init container

The webhook approach ensures pods are mutated before they're created, avoiding the need for deletion and recreation.

## Project Structure

```
nri_balloons_controller/
├── main.go                      # Main entry point
├── pkg/
│   └── webhook/                 # Webhook implementation
│       └── controller/
│           └── pod/
│               └── pod_webhook.go   # Pod mutation logic
├── Dockerfile
├── Makefile
├── go.mod
└── README.md

../../deployment/components/nri-balloons-controller/  # Helm chart
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── serviceaccount.yaml
│   ├── rbac.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml              # Metrics service
│   ├── webhook-service.yaml      # Webhook service
│   ├── certificate.yaml          # cert-manager certificate
│   └── mutatingwebhook.yaml      # MutatingWebhookConfiguration
└── README.md
```

## Quick Start

### 1. Install cert-manager

The webhook requires TLS certificates. Install cert-manager first:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### 2. Build the Controller

```bash
make docker-build
```

### 3. Deploy to Kubernetes

```bash
# Deploy using Helm
cd ../../deployment/components/nri-balloons-controller
helm install nri-balloons-controller . -n nri-balloons-system --create-namespace

# Or use the Makefile shortcut
cd ../../../src/nri_balloons_controller
make helm-install

# Verify deployment
kubectl get pods -n nri-balloons-system
```

### 4. Configure Target Container

The target container name is configured via Helm values:

```bash
helm install nri-balloons-controller ../../deployment/components/nri-balloons-controller \
  -n nri-balloons-system --create-namespace \
  --set config.targetContainerName=my-container
```

## Configuration

### Using Helm

The controller is configured via Helm values. See the [Helm chart README](../../deployment/components/nri-balloons-controller/README.md) for all available configuration options.

Key configuration parameters:

```yaml
config:
  # Target container name to watch for
  targetContainerName: "vllm"
  # Init container configuration
  initContainer:
    image: busybox:latest
    name: nri-balloons-init
  # ConfigMap settings
  configMapName: nri-balloons-config
  configMapNamespace: default
```

Install with custom values:

```bash
helm install nri-balloons-controller ../../deployment/components/nri-balloons-controller \
  -n nri-balloons-system --create-namespace \
  --set config.targetContainerName=my-container
```

## Usage

Once deployed, the webhook automatically:

1. Intercepts pod creation requests
2. Checks if the pod contains a container matching the ConfigMap value
3. Adds the init container to pods that match the criteria
4. Allows the pod to be created with the init container

## Development

### Running Locally

For development, run the operator on your local machine:

```bash
make run
```

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make fmt
```

### Linting

```bash
make vet
```

## Architecture

The controller uses the controller-runtime framework with a mutating webhook:

1. **Webhook Server**: Listens on port 9443 for admission requests
2. **ConfigMap Cache**: Caches target container name from ConfigMap
3. **Pod Mutator**: Implements mutation logic for pod specs
4. **Health Probes**: Exposes `/healthz` and `/readyz` endpoints on port 8081
5. **TLS Certificates**: Managed by cert-manager

### Webhook Flow

```
Pod Creation Request
        ↓
Webhook Intercepts
        ↓
Check Configuration
        ↓
Match Target Container?
        ↓
Has Init Container?
        ↓
No → Ensure ServiceAccount
        ↓
Add Init Container
        ↓
Return Patched Pod
```

## Important Notes

### TLS Certificates

The webhook requires TLS certificates. The manifests include cert-manager resources for automatic certificate management. Ensure cert-manager is installed before deploying.

### Performance

The webhook is called on every pod creation. The ConfigMap is cached to avoid repeated reads. The cache is updated automatically when the ConfigMap changes.

## Troubleshooting

### Check Webhook Logs

```bash
kubectl logs -n nri-balloons-system -l control-plane=controller-manager -f
```

### Verify Webhook Configuration

```bash
kubectl get mutatingwebhookconfigurations nri-balloons-controller-mutating-webhook -o yaml
```

### Check ConfigMap

```bash
kubectl get configmap nri-balloons-config -n default -o yaml
```

### Check events generated by target pods
```bash
kubectl events | grep <target_pod_name>
```

## Uninstallation

```bash
make helm-uninstall
# Or
helm uninstall nri-balloons-controller -n nri-balloons-system
```

This removes all controller resources from the cluster.

## License

Copyright (C) 2024-2026 Intel Corporation
SPDX-License-Identifier: Apache-2.0
