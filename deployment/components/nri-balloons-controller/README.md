# NRI Balloons Controller Helm Chart

This Helm chart deploys the NRI Balloons Controller, a Kubernetes webhook that mutates pods to add init containers, which will wait for NRI balloons Daemonset. 

## Prerequisites

- Kubernetes 1.32.9+
- Helm 3.17+
- cert-manager (for TLS certificate management)

## Installing cert-manager

The webhook requires TLS certificates. Install cert-manager first if not already installed:

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

## Installing the Chart

To install the chart with the release name `nri-balloons-controller`:

```bash
helm install nri-balloons-controller ./nri-balloons-controller -n nri-balloons-system --create-namespace
```

## Uninstalling the Chart

To uninstall/delete the `nri-balloons-controller` deployment:

```bash
helm delete nri-balloons-controller -n nri-balloons-system
```

## Configuration

The following table lists the configurable parameters of the NRI Balloons Controller chart and their default values.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of controller replicas | `1` |
| `image.repository` | Controller image repository | `nri-balloons-controller` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `image.tag` | Image tag | `latest` |
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.name` | Service account name | `""` (auto-generated) |
| `rbac.create` | Create RBAC resources | `true` |
| `config.configMapName` | ConfigMap name for configuration of controller  | `nri-balloons-config` |
| `config.configMapNamespace` | ConfigMap namespace | `default` |
| `config.targetContainerName` | Target container name to watch | `kserve-container` |
| `config.initContainer.image` | Init container image | `erag-init-container` |
| `config.initContainer.name` | Init container name | `wait-for-balloons` |
| `config.balloons.namespace` | Namespace where NRI balloons DaemonSet is deployed | `kube-system` |
| `config.balloons.daemonsetName` | Name of the NRI balloons DaemonSet to wait for | `nri-resource-policy-balloons` |
| `config.balloons.waitTimeout` | Timeout in seconds for waiting for balloons DaemonSet, after that time, pod will fail | `300` |
| `leaderElection.enabled` | Enable leader election | `true` |
| `metrics.enabled` | Enable metrics endpoint | `true` |
| `metrics.port` | Metrics port | `8080` |
| `healthProbe.port` | Health probe port | `8081` |
| `webhook.port` | Webhook server port | `9443` |
| `webhook.service.port` | Webhook service port | `443` |
| `webhook.mutatingWebhookConfiguration.failurePolicy` | Webhook failure policy | `Ignore` |
| `webhook.mutatingWebhookConfiguration.timeoutSeconds` | Webhook timeout | `10` |
| `certManager.enabled` | Enable cert-manager integration | `true` |
| `certManager.certificate.secretName` | TLS certificate secret name | `webhook-server-cert` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |

## Example Values

### Minimal Configuration

```yaml
config:
  targetContainerName: "my-container"
```

### Custom Resources

```yaml
resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 200m
    memory: 256Mi
```

### Custom Init Container

```yaml
config:
  initContainer:
    image: my-registry/my-init:v1.0
    name: custom-init
```

### Node Selector

```yaml
nodeSelector:
  kubernetes.io/os: linux
  node-role.kubernetes.io/control-plane: ""
```

### Tolerations

```yaml
tolerations:
- key: "node-role.kubernetes.io/control-plane"
  operator: "Exists"
  effect: "NoSchedule"
```

## Upgrading

To upgrade the chart:

```bash
helm upgrade nri-balloons-controller . -n nri-balloons-system
```

## Troubleshooting

### Check webhook logs

```bash
kubectl logs -n nri-balloons-system -l app.kubernetes.io/name=nri-balloons-controller -f
```

### Verify webhook configuration

```bash
kubectl get mutatingwebhookconfigurations | grep nri-balloons
kubectl describe mutatingwebhookconfiguration <name>
```

### Check certificates

```bash
kubectl get certificate -n nri-balloons-system
kubectl get secret webhook-server-cert -n nri-balloons-system
kubectl describe certificate -n nri-balloons-system
```

### Test the webhook

Create a test pod with the target container name:

```bash
kubectl run test-pod --image=nginx:latest --overrides='{"spec":{"containers":[{"name":"kserve-container","image":"nginx:latest"}]}}' -n default

# Check if init container was added
kubectl describe pod test-pod -n default | grep -A 10 "Init Containers"

# Cleanup
kubectl delete pod test-pod -n default
```