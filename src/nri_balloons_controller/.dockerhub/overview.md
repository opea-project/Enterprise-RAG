# NRI Balloons Controller

A Kubernetes mutating webhook that ensures selected pods wait for the NRI balloons DaemonSet to be ready.

## 🔍 Overview

The NRI Balloons Controller intercepts Pod creation and mutates pods that contain a specific target container name (configured via ConfigMap / Helm values). For matching pods, it injects an init container that waits until the NRI balloons DaemonSet is ready, helping ensure required node features are available before workloads start.

### Core Capabilities

- Mutating admission webhook for Pod creation
- Target pod selection by container name (configurable)
- Init container injection to gate startup on NRI balloons readiness
- Optional ServiceAccount addition for the init container
- Cached ConfigMap reads for performance

### How It Works

1. Webhook intercepts Pod creation requests
2. Reads target container name from cached configuration
3. Checks whether the pod contains the target container
4. If matched (and init container is not already present), injects the init container
5. Returns a patched Pod spec to Kubernetes

## Related Components

This controller is typically deployed alongside:
- NRI balloons DaemonSet
- cert-manager (for webhook TLS certificates)
- Helm chart manifests (MutatingWebhookConfiguration, RBAC, Service, Deployment)

## License

OPEA ERAG is licensed under the Apache License, Version 2.0.

Copyright © 2024–2025 Intel Corporation. All rights reserved.
