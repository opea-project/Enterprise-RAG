# Namespace Status Watcher Microservice

This microservice provides Kubernetes namespace status monitoring functionality, retrieving the status of all resources deployed in a specified namespace. It queries the Kubernetes API to discover and report on ConfigMaps, Services, Deployments, StatefulSets, ServiceAccounts, PersistentVolumeClaims, and HorizontalPodAutoscalers.

## Table of Contents

1. [Namespace Status Watcher Microservice](#namespace-status-watcher-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [🚀 Start Namespace Status Watcher Microservice with Python (Option 1)](#-start-namespace-status-watcher-microservice-with-python-option-1)
     - 3.1.1. [Install Requirements](#install-requirements)
     - 3.1.2. [Start Microservice](#start-microservice)
   - 3.2. [🚀 Start Namespace Status Watcher Microservice with Docker (Option 2)](#-start-namespace-status-watcher-microservice-with-docker-option-2)
     - 3.2.1. [Build the Docker Image](#build-the-docker-image)
     - 3.2.2. [Run the Docker Container](#run-the-docker-container)
   - 3.3. [Verify the Namespace Status Watcher Microservice](#verify-the-namespace-status-watcher-microservice)
     - 3.3.1. [Check Status](#check-status)
     - 3.3.2. [Sending a Request](#sending-a-request)
       - 3.3.2.1. [Example Request](#example-request)
       - 3.3.2.2. [Example Output](#example-output)
## Configuration Options

The configuration for the Namespace Status Watcher Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                  | Default               |
|-----------------------------|--------------------------------------------------------------|-----------------------|
| `TARGET_NAMESPACE`          | The Kubernetes namespace to monitor                          | audio                 |
| `NAMESPACE_STATUS_WATCHER_PORT`     | The port of the microservice                                 | 9010                  |
| `OPEA_LOGGER_LEVEL`         | Logger level for the microservice                            | INFO                  |

## Getting Started

There are 2 ways to run this microservice:
  - [via Python](#-start-namespace-status-watcher-microservice-with-python-option-1)
  - [via Docker](#-start-namespace-status-watcher-microservice-with-docker-option-2) **(recommended)**

### 🚀 Start Namespace Status Watcher Microservice with Python (Option 1)

To start the Namespace Status Watcher microservice, installing all the dependencies first is required.

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python opea_namespace_status_watcher_microservice.py
```

The microservice will start and listen on the configured port (default: 9010).

### 🚀 Start Namespace Status Watcher Microservice with Docker (Option 2)

#### Build the Docker Image

Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/namespace-status-watcher:latest -f comps/namespace_status_watcher/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container

```bash
docker run -d --name namespace-status-watcher-microservice \
  --net=host \
  --ipc=host \
  opea/namespace-status-watcher:latest
```

### Verify the Namespace Status Watcher Microservice

#### Check Status

To verify that the microservice is running correctly, you can check its health:

```bash
curl http://localhost:9010/v1/health_check
```

#### Sending a Request

##### Example Request

To get the status of all resources in the configured namespace, when `TARGET_NAMESPACE` equals audio:

```bash
curl -X GET http://localhost:9010/v1/audio/status
```

##### Example Output

```json
{
  "status": {
    "annotations": {
      "ConfigMap:v1:audio-asr-config:audio": "provisioned",
      "ConfigMap:v1:audio-tts-config:audio": "provisioned",
      "ConfigMap:v1:audio-tts-fastapi-configmap:audio": "provisioned",
      "ConfigMap:v1:audio-vllm-configmap:audio": "provisioned",
      "ConfigMap:v1:istio-ca-crl:audio": "provisioned",
      "ConfigMap:v1:istio-ca-root-cert:audio": "provisioned",
      "ConfigMap:v1:kube-root-ca.crt:audio": "provisioned",
      "Service:v1:asr-svc:audio": "http://asr-svc.audio.svc:9009",
      "Service:v1:namespace-status-watcher-svc:audio": "http://namespace-status-watcher-svc.audio.svc:9010",
      "Service:v1:tts-fastapi-model-server:audio": "http://tts-fastapi-model-server.audio.svc:8008",
      "Service:v1:tts-svc:audio": "http://tts-svc.audio.svc:9009",
      "Service:v1:vllm-audio-cpu:audio": "http://vllm-audio-cpu.audio.svc:8008",
      "Deployment:apps/v1:asr-svc:audio": "Ready; Replicas: 1 desired | 1 ready | 1 available | 1 updated\n  Type: Available\n  Status: True\n  Reason: MinimumReplicasAvailable\n  Message: Deployment has minimum availability.\n  Type: Progressing\n  Status: True\n  Reason: NewReplicaSetAvailable\n  Message: ReplicaSet \"asr-svc-8495cfc46f\" has successfully progressed.\n",
      "Deployment:apps/v1:namespace-status-watcher-svc:audio": "Ready; Replicas: 1 desired | 1 ready | 1 available | 1 updated\n  Type: Progressing\n  Status: True\n  Reason: NewReplicaSetAvailable\n  Message: ReplicaSet \"namespace-status-watcher-svc-67745fcbfb\" has successfully progressed.\n  Type: Available\n  Status: True\n  Reason: MinimumReplicasAvailable\n  Message: Deployment has minimum availability.\n",
      "Deployment:apps/v1:tts-fastapi-model-server:audio": "Ready; Replicas: 1 desired | 1 ready | 1 available | 1 updated\n  Type: Available\n  Status: True\n  Reason: MinimumReplicasAvailable\n  Message: Deployment has minimum availability.\n  Type: Progressing\n  Status: True\n  Reason: NewReplicaSetAvailable\n  Message: ReplicaSet \"tts-fastapi-model-server-679c7ff9dc\" has successfully progressed.\n",
      "Deployment:apps/v1:tts-svc:audio": "Ready; Replicas: 1 desired | 1 ready | 1 available | 1 updated\n  Type: Available\n  Status: True\n  Reason: MinimumReplicasAvailable\n  Message: Deployment has minimum availability.\n  Type: Progressing\n  Status: True\n  Reason: NewReplicaSetAvailable\n  Message: ReplicaSet \"tts-svc-5c6b894bb9\" has successfully progressed.\n",
      "Deployment:apps/v1:vllm-audio-cpu:audio": "Ready; Replicas: 1 desired | 1 ready | 1 available | 1 updated\n  Type: Available\n  Status: True\n  Reason: MinimumReplicasAvailable\n  Message: Deployment has minimum availability.\n  Type: Progressing\n  Status: True\n  Reason: NewReplicaSetAvailable\n  Message: ReplicaSet \"vllm-audio-cpu-7fdc6dd95b\" has successfully progressed.\n",
      "ServiceAccount:v1:asr:audio": "provisioned",
      "ServiceAccount:v1:namespace-status-watcher-sa:audio": "provisioned",
      "ServiceAccount:v1:tts:audio": "provisioned",
      "ServiceAccount:v1:tts-fastapi-model-server:audio": "provisioned",
      "ServiceAccount:v1:vllm-audio-cpu:audio": "provisioned"
    }
  }
}
```
