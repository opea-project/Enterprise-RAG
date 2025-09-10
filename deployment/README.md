# Deploy Intel&reg; AI for Enterprise RAG

This document details the deployment of Intel® AI for Enterprise RAG. By default, the guide assumes a Xeon + Gaudi deployment. If you are deploying on Xeon-only hardware, please follow the Xeon-only instructions marked throughout this guide.

## Table of Contents

1. [Verify System Status](#verify-system-status)
   1. [Xeon + Gaudi (Default)](#xeon--gaudi-default)
   2. [Xeon-Only](#xeon-only)
2. [Preconfigure the Environment](#preconfigure-the-environment)
3. [Prepare Configuration Files](#prepare-configuration-files)
   1. [Prepare Main Configuration File](#prepare-main-configuration-file)
   2. [Storage](#storage)
   3. [Defining Resources for Your Machine](#defining-resources-for-your-machine)
   4. [Skipping Warm-up for vLLM Deployment](#skipping-warm-up-for-vllm-deployment)
   5. [Additional Settings for Running Telemetry](#additional-settings-for-running-telemetry)
4. [Configure the Environment](#configure-the-environment)
5. [Docker Images](#docker-images)
   1. [Build and Push Images](#build-and-push-images)
6. [Deployment Options](#deployment-options)
   1. [Installation](#installation)
   2. [Verify Services](#verify-services)
7. [Interact with ChatQnA](#interact-with-chatqna)
   1. [Test Deployment](#test-deployment)
   2. [Access the UI/Grafana](#access-the-uigrafana)
   3. [UI Credentials for the First Login](#ui-credentials-for-the-first-login)
   4. [Credentials for Grafana and Keycloak](#credentials-for-grafana-and-keycloak)
   5. [Credentials for Vector Store](#credentials-for-vector-store)
   6. [Credentials for Enhanced Dataprep Pipeline (EDP)](#credentials-for-enhanced-dataprep-pipeline-edp)
   7. [Data Ingestion, UI, and Telemetry](#data-ingestion-ui-and-telemetry)
8. [Configure ChatQnA](#configure-chatqna)
9. [Clear All](#clear-all)
10. [Additional Features](#additional-features)
    1. [Enabling Horizontal Pod Autoscaling](#enabling-horizontal-pod-autoscaling)
    2. [Enabling Pod Security Admission (PSA)](#enabling-pod-security-admission-psa)
    3. [Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)](#running-enterprise-rag-with-intel-trust-domain-extensions-intel-tdx)
    4. [Redis Vector Database Performance Settings](#redis-vector-database-performance-settings)
    5. [Vector Database RBAC support](#vector-database-rbac-support)
    6. [Single Sign-On Integration Using Microsoft Entra ID](#single-sign-on-integration-using-microsoft-entra-id-formerly-azure-active-directory)
    7. [Backup Functionality with VMWare Velero](#backup-functionality-with-vmware-velero)
11. [Additional Pipelines](#additional-pipelines)
    1. [Language Translation Pipeline](#language-translation-pipeline)
---

## Verify System Status

Before proceeding, run the following command:
```bash
kubectl get pods -A
```
This command verifies that all necessary Kubernetes components are running.

### Xeon + Gaudi (Default)
The expected output should include pods in the following namespaces:

- `kube-system`: Calico, Kube-apiserver, Kube-controller-manager, Kube-scheduler, DNS, and NodeLocalDNS
- `habana-system`: Habana device plugin
- `local-path-storage`: Local path provisioner

For example, your output might look similar to:
```
NAMESPACE            NAME                                       READY   STATUS    RESTARTS   AGE
habana-system        habanalabs-device-plugin-daemonset-hbkwp   1/1     Running   0          5d8h
kube-system          calico-kube-controllers-68485cbf9c-8cnhr   1/1     Running   0          5d9h
kube-system          calico-node-sncgd                          1/1     Running   0          5d9h
kube-system          coredns-69db55dd76-gsvhx                   1/1     Running   0          5d9h
kube-system          dns-autoscaler-6d5984c657-mz8dx            1/1     Running   0          5d9h
kube-system          kube-apiserver-node1                       1/1     Running   1          5d9h
kube-system          kube-controller-manager-node1              1/1     Running   2          5d9h
kube-system          kube-proxy-t8ndk                           1/1     Running   0          5d9h
kube-system          kube-scheduler-node1                       1/1     Running   1          5d9h
kube-system          nodelocaldns-82kgx                         1/1     Running   0          5d9h
local-path-storage   local-path-provisioner-f78b6cbbc-cqw9m     1/1     Running   0          5d9h
```

### Xeon-Only

For Xeon-only deployments, the `habana-system` namespace will not be present. In this case, the expected output should include only:

  - `kube-system`: Calico, Kube-apiserver, Kube-controller-manager, Kube-scheduler, DNS, and NodeLocalDNS
  - `local-path-storage`: Local path provisioner

If your output does not match these expectations, please refer to the [prerequisites](../docs/prerequisites.md) guide.

> [!NOTE]
> The example above uses the [Local Path Provisioner CSI driver](https://github.com/rancher/local-path-provisioner). Any CSI driver supporting **`ReadWriteOnce`** (single-node clusters) or **`ReadWriteMany`** (multi-node clusters) may be used. See [Storage Class](#storage-class) for details.

---

## Preconfigure the Environment

It is recommended to use python3-venv to manage Python packages:

```sh
sudo apt-get install python3-venv
python3 -m venv erag-venv
source erag-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yaml --upgrade
```

---

## Prepare Configuration Files

### Prepare Main Configuration File

To prepare the configuration file, create a copy of the example one:

```sh
cp -r inventory/sample inventory/test-cluster
```

Fill in the appropriate variables in `inventory/test-cluster/config.yaml`:

```yaml
# uses kubespray to deploy Kubernetes cluster and install required components
deploy_k8s: false
# local path provisioner works only with kubespray deployment, so deploy_k8s needs to be true to install it.
install_csi: "local-path-provisioner" # available options: "local-path-provisioner"

gaudi_operator: false # set to true when Gaudi operator is to be installed

huggingToken: FILL_HERE # Provide your Hugging Face token here
kubeconfig: FILL_HERE # Provide the absolute path to your kubeconfig file

httpProxy:
httpsProxy:
# If HTTP/HTTPS proxy is set, update the noProxy field with the following:
noProxy: #"localhost,.svc,.monitoring,.monitoring-traces"

FQDN: "erag.com" # Provide the FQDN for the deployment

# If you want to use certificates, set autoGenerated to false and provide the paths to the cert and key
certs:
  autoGenerated: true # Generate self-signed certs
  pathToCert: "" # Provide absolute path to cert
  pathToKey: "" # Provide absolute path to key

registry: "docker.io/opea" # alternatively "localhost:5000/erag" for local registry
tag: "1.4.0"
setup_registry: true # this is localhost registry that may be used for localhost one-node deployment
use_alternate_tagging: false # changes format of images from registry/image:tag to registry:image_tag
helm_timeout: "10m0s"

hpaEnabled: false # enables Horizontal Pod Autoscaler
enforcePSS: false # enforces Pod Security Standards

tdx: # enables Intel® Trust Domain Extensions
  enabled: false
  td_type: one-td # one-td/coco
  attestation:
      enabled: false

llm_model: "casperhansen/llama-3-8b-instruct-awq"
llm_model_gaudi: "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Topology-aware resource scheduling and CPU pinning for vLLM
# For detailed documentation, refer to: deployment/components/nri-plugin/README.md
balloons:
  enabled: false
  namespace: kube-system # alternatively, set custom namespace for balloons

pipelines:
  - namespace: chatqa
    samplePath: chatqa/reference-cpu.yaml
    resourcesPath: chatqa/resources-reference-cpu.yaml
    modelConfigPath: chatqa/resources-model-cpu.yaml
    type: chatqa

gmc:
  enabled: true
  namespace: system

ingress:
  enabled: true
  service_type: NodePort # Set it accordingly to environment if Loadbalancer is supported
  namespace: ingress-nginx

keycloak:
  enabled: true
  namespace: auth
  domainName: auth.erag.com

apisix:
  enabled: true
  namespace: auth-apisix

istio:
  enabled: true
  namespace: istio-system

telemetry:
  enabled: true
  domainName: grafana.erag.com
  monitoring:
    namespace: monitoring
  traces:
    namespace: monitoring-traces

ui:
  enabled: true
  domainName: erag.com
  namespace: rag-ui

edp:
  enabled: true
  namespace: edp
  dpGuard:
    enabled: false
  storageType: minio
  minio:
    domainName: minio.erag.com
    apiDomainName: s3.erag.com
    bucketNameRegexFilter: ".*"
  s3:
    region: "us-east-1"
    accessKeyId: ""
    secretAccessKey: ""
    sqsEventQueueUrl: ""
    bucketNameRegexFilter: ".*"
  s3compatible:
    region: "us-east-1"
    accessKeyId: ""
    secretAccessKey: ""
    internalUrl: "https://s3.example.com"
    externalUrl: "https://s3.example.com"
    bucketNameRegexFilter: ".*"

fingerprint:
  enabled: true
  namespace: fingerprint

```

> [!NOTE]
> Balloons policy is not supported on Gaudi or non-NUMA architectures.
> For more informations regarding balloons policy refer [here](components/nri-plugin/README.md)

> [!NOTE]
> The default LLM for Xeon execution is `casperhansen/llama-3-8b-instruct-awq`.
> Ensure your HUGGINGFACEHUB_API_TOKEN grants access to this model.
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.

> [!NOTE]
> To achieve optimal performance on Intel® Xeon® processors, additional configuration adjustments may be required.
> For detailed guidance, refer to the [Performance tuning tips](../docs/performance_tuning_tips.md).


### Storage
#### Storage Class
Users can define their own CSI driver that will be used during deployment. The StorageClass should support accessMode ReadWriteMany (RWX).

> [!WARNING]
> If the driver does not support ReadWriteMany accessMode and Enterprise RAG is deployed on a multi-node cluster, pods may hang in `container creating` state for `tei-reranking` or `vllm`. This occurs because these pods use the same PVC `model-volume-llm` and only one pod can access it if pods are on different nodes. This issue can be worked around by defining another PVC entry in [values.yaml](./components/gmc/microservices-connector/helm/values.yaml) and using it in the reranking manifest: [teirerank.yaml](./components/gmc/microservices-connector/config/manifests/teirerank.yaml) in the volumes section. However, we strongly recommend using a StorageClass that supports ReadWriteMany accessMode.

We recommend setting `volumeBindingMode` to `WaitForFirstConsumer`

#### Setting Default Storage Class
Before running the Enterprise RAG solution, ensure that you have set the correct StorageClass as the default one. You can list storage classes using the following command:

```bash
kubectl get sc -A
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  12d
```

To set a specific storage class as the default, use the following command:
```bash
kubectl patch storageclass <storage_class_name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
Additionally, ensure that the `pvc` section in [values.yaml](./components/gmc/microservices-connector/helm/values.yaml) matches your chosen storage class's capabilities.

#### Storage Settings

> [!NOTE]
> The default settings are suitable for smaller deployments only (by default, approximately 5GB of data).

You can expand the storage configuration for both the Vector Store and MinIO deployments by modifying their respective configurations:

If using EDP, update the `deployment/edp/values.yaml` file to increase the storage size under the `persistence` section. For example, set `size: 100Gi` to allocate 100Gi of storage.

Similarly, for the selected Vector Store you can increase the persistent storage size. This configration is available in `deployment/compnents/vector_databases/values.yaml` For example, set `persistence.size: 100Gi` to allocate 100Gi of storage for VectorStore database data.

> [!NOTE]
> The Vector Store storage should have more storage than file storage due to containing both extracted text and vector embeddings for that data.

#### EDP Storage Types

By default, the EDP storage type is set to MinIO, which deploys MinIO and S3 in-cluster. For additional options, refer to the [EDP documentation](../src/edp/README.md).

### Defining Resources For Your Machine

The default resource allocations are defined for CPU-only deployment in [`resources-reference-cpu.yaml`](./pipelines/chatqa/resources-reference-cpu.yaml) or for CPU and Gaudi in [`resources-reference-hpu.yaml`](./pipelines/chatqa/resources-reference-hpu.yaml).

> [!NOTE]
> It is possible to reduce the resources allocated to the model server if you encounter issues with node capacity, but this will likely result in a performance drop. Recommended hardware parameters to run RAG pipeline are available [here](../README.md#hardware-prerequisites-for-deployment-using-xeon-only).

> [!NOTE]
> Enterprise RAG supports autoscaling of pods using Horizontal Pod Autoscalers (HPA). For details on how to configure the `hpa` section, refer to [Horizontal Pod Autoscaler](#enabling-horizontal-pod-autoscaling).


For Enhanced Dataprep Pipeline (EDP) configuration, please refer to the separate Helm chart located in the `deployment/components/edp` folder. It does not have a separate `resources*.yaml` definition. To change resources before deployment, edit the [`values.yaml`](./components/edp/values.yaml) file for particular elements in that deployment.

### Skipping Warm-up for vLLM Deployment
The `VLLM_SKIP_WARMUP` environment variable controls whether the model warm-up phase is skipped during initialization. To modify this setting, update the deployment configuration in:
  - For vLLM running on Gaudi: [vllm/docker/.env.hpu](../src/comps/llms/impl/model_server/vllm/docker/hpu/.env)
  - For vLLM running on CPU: [vllm/docker/.env.cpu](../src/comps/llms/impl/model_server/vllm/docker/cpu/.env)

> [!NOTE]
> By default, `VLLM_SKIP_WARMUP` is set to True on Gaudi to reduce startup time.

### Additional Settings for Running Telemetry

Enterprise RAG includes the installation of a telemetry stack by default, which requires setting the number of iwatch open descriptors on each cluster host. For more information, follow the instructions in [Number of iwatch open descriptors](./components/telemetry/helm/charts/logs/README.md#1b-number-of-iwatch-open-descriptors).

---

## Configure the Environment
To prepare your environment for development and deployment, run the following command:

```sh
ansible-playbook -u $USER -K playbooks/application.yaml --tags configure -e @inventory/test-cluster/config.yaml
```

This command will configure various tools in your environment, including `Docker`, `Helm`, `make`, `zip`, and `jq`.

> [!NOTE]
> Before running the script, please be aware that it uses `sudo` privileges to install the mentioned packages and configure settings. Please use with caution, as this may overwrite existing configurations.

---

## Docker Images

Deployment utilizes Docker images - check [docker images list](../docs/docker_images_list.md) for detailed information. 

Prebuilt images for Enterprise RAG components are publicly available on [OPEA Docker Hub](https://hub.docker.com/u/opea?page=1&search=erag) and are used by default, as defined by the  `registry` and `tag` values in [inventory/sample/config.yaml](inventory/sample/config.yaml).

Deployment is based on released docker images - check [Docker images list](../docs/docker_images_list.md) for detailed information.

If you prefer to build the images manually and push them to a private registry, follow the steps below. Then, update the registry and tag values in your `config.yaml` file accordingly to point to them.

### Build and Push Images

The `update_images.sh` script is responsible for building the images for these microservices from source and pushing them to a specified registry. The script consists of three main steps: build images, set up the registry, and push the images. To execute all at once, run:
```bash
./update_images.sh --build --setup-registry --push
```

Alternatively, you can run each step separately. Below is a detailed description of each step, along with additional options. You can also run `./update_images.sh --help` for more information.

#### Step 1: Build

The first step is to build the images for each microservice component using the source code. This involves compiling the code, packaging it into Docker images, and performing any necessary setup tasks.

```bash
./update_images.sh --build
```

> [!NOTE]
> - You can build individual images, for example `./update_images.sh --build embedding-usvc reranking-usvc` which only builds the embedding and reranking images.
> - To list all available image names, run `./update_images.sh --help` and refer to the "Components Available" section.
> - Use `-j <number of concurrent tasks>` parameter to increase the number of concurrent tasks.
> - Use `--tag <your tag>` to set a custom image tag. Defaults to `latest` if not specified.

#### Step 2: Setup Registry

The second step is to configure the registry where the built images will be pushed. This may involve
setting up authentication, specifying the image tags, and defining other configuration parameters.

```bash
./update_images.sh --setup-registry
```

By default, the registry is set to `localhost:5000` You can change this by specifying a different registry using the `--registry` option.

#### Step 3: Push

The final step is to push the built images to the configured registry. This ensures that the images are
deployed to the desired environment and can be accessed by the application.

```bash
./update_images.sh --push
```


---

## Deployment Options

### Installation

With the configuration file in place, run:

```sh
ansible-playbook -u $USER -K playbooks/application.yaml --tags install -e @inventory/test-cluster/config.yaml
```

After successful playbook completion, proceed to [Verify Services](#verify-services) to check if the deployment is successful.

## Verify Services

Run `kubectl get pods -A` to verify that the expected pods are running.

<details>
<summary>
Click here to verify that the output looks as below:
</summary>
<pre>
NAMESPACE            NAME                                                    READY   STATUS      RESTARTS       AGE
auth-apisix          auth-apisix-6b99bbb7d7-xwrm6                            1/1     Running     0              24m
auth-apisix          auth-apisix-etcd-0                                      1/1     Running     0              24m
auth-apisix          auth-apisix-ingress-controller-6b9c4bffbb-kp2zp         1/1     Running     0              24m
auth                 keycloak-0                                              1/1     Running     0              26m
auth                 keycloak-postgresql-0                                   1/1     Running     0              26m
chatqa               embedding-svc-deployment-5986c5b57f-wmx48               1/1     Running     0              21m
chatqa               fgp-svc-deployment-6988d6d6d7-ph8vq                     1/1     Running     0              21m
chatqa               input-scan-svc-deployment-56dcc86576-2xtjs              1/1     Running     0              21m
chatqa               llm-svc-deployment-5d7c4784c9-cxl6f                     1/1     Running     0              21m
chatqa               output-scan-svc-deployment-96b855b76-94lpk              1/1     Running     0              21m
chatqa               prompt-template-svc-deployment-fc864d889-dfxfh          1/1     Running     0              21m
chatqa               redis-vector-db-deployment-8557855f6f-9kpsq             1/1     Running     0              21m
chatqa               reranking-svc-deployment-746c8fbb4d-vdhzl               1/1     Running     0              21m
chatqa               retriever-svc-deployment-7b59f867c4-xv22r               1/1     Running     0              21m
chatqa               router-service-deployment-849f64848d-6vbsq              1/1     Running     0              21m
chatqa               tei-reranking-svc-deployment-7f85654f8b-bvj9j           1/1     Running     0              21m
chatqa               torchserve-embedding-svc-deployment-54d498dd6f-78mtv    1/1     Running     0              21m
chatqa               torchserve-embedding-svc-deployment-54d498dd6f-btg2l    1/1     Running     0              21m
chatqa               torchserve-embedding-svc-deployment-54d498dd6f-hwfz4    1/1     Running     0              21m
chatqa               torchserve-embedding-svc-deployment-54d498dd6f-jqcfh    1/1     Running     0              21m
chatqa               vllm-service-m-deployment-6d86b69fb-6xxr2               1/1     Running     0              21m
edp                  edp-backend-559948896d-f9xkq                            1/1     Running     0              13m
edp                  edp-celery-7b999df6fb-p7j84                             1/1     Running     1 (7m4s ago)   13m
edp                  edp-dataprep-76b895d445-wh629                           1/1     Running     0              13m
edp                  edp-embedding-844f9c9c97-tq49m                          1/1     Running     0              13m
edp                  edp-flower-554594dd4d-6z666                             1/1     Running     0              13m
edp                  edp-ingestion-bc559885f-s7qsp                           1/1     Running     0              13m
edp                  edp-minio-5948fbc87f-6d8lq                              1/1     Running     0              13m
edp                  edp-minio-provisioning-7rx98                            0/1     Completed   0              12m
edp                  edp-postgresql-0                                        1/1     Running     0              13m
edp                  edp-redis-master-0                                      1/1     Running     0              13m
fingerprint          fingerprint-mongodb-7657456488-vg9qj                    1/1     Running     0              22m
fingerprint          fingerprint-svc-7447b8b6df-w4q75                        1/1     Running     0              22m
ingress-nginx        ingress-nginx-controller-5f54f7f779-sfnlv               1/1     Running     0              15m
istio-system         istio-cni-node-sjp55                                    1/1     Running     0              26m
istio-system         istiod-5bcbd9f7bc-fmtwx                                 1/1     Running     0              26m
istio-system         ztunnel-k275b                                           1/1     Running     0              26m
kube-system          calico-kube-controllers-68485cbf9c-vq94k                1/1     Running     16 (68d ago)   74d
kube-system          calico-node-sfjbk                                       1/1     Running     0              75d
kube-system          coredns-69db55dd76-gbtzm                                1/1     Running     0              74d
kube-system          dns-autoscaler-6d5984c657-zqvn8                         1/1     Running     0              74d
kube-system          kube-apiserver-node1                                    1/1     Running     1              75d
kube-system          kube-controller-manager-node1                           1/1     Running     2              75d
kube-system          kube-proxy-pfc7m                                        1/1     Running     0              75d
kube-system          kube-scheduler-node1                                    1/1     Running     1              75d
kube-system          nodelocaldns-wgvhm                                      1/1     Running     1 (21d ago)    75d
local-path-storage   local-path-provisioner-f78b6cbbc-5rcc5                  1/1     Running     0              74d
monitoring-traces    otelcol-traces-collector-66dd5648b6-wvs6f               1/1     Running     0              8m
monitoring-traces    telemetry-traces-otel-operator-8665c5f949-7754t         2/2     Running     0              9m5s
monitoring-traces    telemetry-traces-tempo-0                                1/1     Running     0              9m4s
monitoring           alertmanager-telemetry-kube-prometheus-alertmanager-0   2/2     Running     0              11m
monitoring           habana-metric-exporter-ds-9tqr9                         1/1     Running     0              11m
monitoring           loki-canary-cgj4k                                       1/1     Running     0              10m
monitoring           prometheus-telemetry-kube-prometheus-prometheus-0       2/2     Running     0              11m
monitoring           telemetry-grafana-7644d9d67d-qwnp9                      3/3     Running     0              11m
monitoring           telemetry-kube-prometheus-operator-b55bd6df6-7649p      1/1     Running     0              11m
monitoring           telemetry-kube-state-metrics-79c9bf5669-f2k7r           1/1     Running     0              11m
monitoring           telemetry-logs-loki-0                                   2/2     Running     0              10m
monitoring           telemetry-logs-loki-chunks-cache-0                      2/2     Running     0              10m
monitoring           telemetry-logs-loki-gateway-6767655445-vpft9            1/1     Running     0              10m
monitoring           telemetry-logs-loki-results-cache-0                     2/2     Running     0              10m
monitoring           telemetry-logs-minio-0                                  1/1     Running     0              10m
monitoring           telemetry-logs-otelcol-logs-agent-p9kpj                 1/1     Running     0              10m
monitoring           telemetry-prometheus-node-exporter-99k2t                1/1     Running     0              11m
monitoring           telemetry-prometheus-redis-exporter-64d9d6f989-d4w64    1/1     Running     0              11m
rag-ui               ui-chart-5b98cb4c54-k58ck                               1/1     Running     0              14m
system               gmc-contoller-5d7d8b49bf-xj9zv                          1/1     Running     0              22m
</pre>
</details>

---

## Interact with ChatQnA

### Test Deployment

To verify that the deployment was successful, run the following command:
```bash
./scripts/test_connection.sh
```
If the deployment is complete, you should observe the following output:
```
deployment.apps/client-test created
Waiting for all pods to be running and ready....All pods in the chatqa namespace are running and ready.
Connecting to the server through the pod client-test-87d6c7d7b-45vpb using URL http://router-service.chatqa.svc.cluster.local:8080...
data: '\n'
data: 'A'
data: ':'
data: ' AV'
data: 'X'
data: [DONE]
Test finished successfully
```

### Access the UI/Grafana

To access the UI, follow these steps:
1. Forward the port from the ingress pod:
    ```bash
    sudo -E kubectl port-forward --namespace ingress-nginx svc/ingress-nginx-controller 443:https
    ```
2. If you want to access the UI from another machine, tunnel the port from the host:
    ```bash
    ssh -L 443:localhost:443 user@ip
    ```
3. Update the `/etc/hosts` file on the machine where you want to access the UI to match the domain name with the externally exposed IP address of the cluster. On a Windows machine, this file is typically located at `C:\Windows\System32\drivers\etc\hosts`.

    For example, the updated file content should resemble the following:

    ```
    127.0.0.1 erag.com grafana.erag.com auth.erag.com s3.erag.com minio.erag.com
    ```

    > [!NOTE]
    > This is the IPv4 address of the local machine.


Once the update is complete, you can access the Enterprise RAG UI by typing the following URL in your web browser:
`https://erag.com`

Keycloak can be accessed via:
`https://auth.erag.com`

Grafana can be accessed via:
`https://grafana.erag.com`

MinIO Console can be accessed via:
`https://minio.erag.com`

S3 API is exposed at:
`https://s3.erag.com`

> [!CAUTION]
> Before ingesting data, access `https://s3.erag.com` to agree to accessing the self-signed certificate.

### UI Credentials for the First Login

Once deployment is complete, a file named `default_credentials.txt` will be created in the `deployment/ansible-logs` folder with one-time passwords for the application admin and user. After entering the one-time password, you will be required to change the default password.

> [!CAUTION]
> Please remove the `default_credentials.txt` file after the first successful login.

### Credentials for Grafana and Keycloak

Default credentials for Keycloak and Grafana:
- **username:** admin
- **password:** stored in `ansible-logs/default_credentials.yaml` file. Please change passwords after first login in Grafana or Keycloak.

> [!CAUTION]
> Please use ansible-vault to secure the password file `ansible-logs/default_credentials.yaml` after the first successful login by running:
> `ansible-vault encrypt ansible-logs/default_credentials.yaml`. After that, remember to add `-ask-vault-pass` to the `ansible-playbook` command.

### Credentials for Vector Store

Default credentials for the selected Vector Store are stored in `ansible-logs/default_credentials.yaml` and are generated on first deployment.

### Credentials for Enhanced Dataprep Pipeline (EDP)

Default credentials for Enhanced Dataprep services:

MinIO:
- For accessing MinIO either by API or Web-UI (MinIO Console), please use the user credentials for `erag-admin`.

Internal EDP services credentials:

Redis:
- **username:** default
- **password:** stored in `ansible-logs/default_credentials.yaml`

Postgres:
- **username:** edp
- **password:** stored in `ansible-logs/default_credentials.yaml`

### Data Ingestion, UI and Telemetry

For adding data to the knowledge base and exploring the UI interface, visit [this](../docs/UI_features.md) page.

For accessing Grafana dashboards for all services, visit [this](../docs/telemetry.md) page.

---

## Clear All
Run this command to delete all namespaces, releases, and services associated with the ChatQNA pipeline:
```sh
ansible-playbook playbooks/application.yaml --tags uninstall -e @inventory/test-cluster/config.yaml
```

---

## Additional Features

### Enabling Horizontal Pod Autoscaling

This feature enables an automated scaling mechanism for pipeline components that might become bottlenecks for the RAG pipeline. The components are scaled up based on rules defined in the `hpa` section of [resources-reference-cpu](./pipelines/chatqa/resources-reference-cpu.yaml) when running on Xeon or [resources-reference-hpu](./pipelines/chatqa/resources-reference-hpu.yaml) when running on Gaudi.

To enable HPA, set `hpaEnabled` to true in the [configuration file](#prepare-main-configuration-file).
For more information on how to set parameters in the HPA section, please refer to this [README](./hpa/README.md).

To update your HPA configuration:
1. Modify the `hpa` section in the resources file
2. Run the installation command:
```sh
ansible-playbook playbooks/application.yaml --tags install -e @inventory/test-cluster/config.yaml
```

For detailed information on how to configure the pipeline, please refer to:
[configure_pipeline](./../docs/configure_pipeline.md)

### Enabling Pod Security Admission (PSA)
Pod Security Admission (PSA) is a built-in admission controller that enforces the Pod Security Standards (PSS). These standards define different isolation levels for pods to ensure security and compliance within a cluster. PSA operates at the namespace level and uses labels to enforce policies on pods when they are created or updated.

We can deploy Enterprise RAG with enforced validation of PSS across all deployed namespaces. To enable PSA, set `enforcePSS` to `true` in the [configuration file](#prepare-main-configuration-file).

### Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

For deploying ChatQnA components with Intel® Trust Domain Extensions (Intel® TDX), refer to the [Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)](../docs/tdx.md) guide.

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.

### Redis Vector Database Performance Settings

If you want to store more data resulting in >1M vectors, it is strongly encouraged to deploy the solution using `redis-cluster` vector store rather than plain `redis`. This allows horizontal partitioning over multiple redis instances. Number of instances is configurable via either the helm chart, or directly via `deployment/inventory/**/config.yaml` as follows:

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster
  redis-cluster:
    nodes: 3
    replicas: 0
```
In addition, larger databases might benefit from different vector store index configuration, such as changing the search algorithm from `FLAT` to `HNSW`. This is configurable via `deployment/inventory/**/config.yaml` as follows:

```yaml
edp:
  ingestion:
    config:
      vector_algorithm: "HNSW"
      vector_datatype: "FLOAT32"
      vector_distance_metric: "COSINE"
      # For HNSW Algorithm additional settings are available
      vector_hnsw_m: "32"
      vector_hnsw_ef_construction: "32"
      vector_hnsw_ef_runtime: "32"
      vector_hnsw_epsilon: "0.01"
```

Please note that changing those settings requires additional RAM and storage for the vector database, since it creates additional indexes without removing the already existing ones. This operation might be time-consuming, depending on the amount of data already stored in the database.

Please ensure the Redis instances have enough resources assigned, both from compute and storage. This is configurable via `deployment/inventory/**/config.yaml` as follows:

```yaml
vector_databases:
  enabled: true
  namespace: vdb
  vector_store: redis-cluster
  redis-cluster:
    persistence:
      size: "30Gi"
    resources:
      requests:
        cpu: 8
        memory: 16Gi
      limits:
        cpu: 16
        memory: 128Gi
```

In case of `redis-cluster`, all above settings are applied for each cluster node.

### Vector Database RBAC support

EDP backend is responsible for processing the request and returning validated buckets accesses for pipeline requests. By enabling it in edp, pipeline retriever's config-map is also updated to enable this feature. Depending of the validation type selected, storage endpoint is queried validated for current user's storage access to buckets. Storage endpoint is used as the source of truth for user access.

Enabling of RBAC is configurable via `deployment/inventory/**/config.yaml`, for example to enable most strict validation (validate on each request) use:

```yaml
edp:
  rbac:
    enabled: true
    validationType: "ALWAYS"
```

For more detail and configuration options refer to [EDP's documentation](../src/edp/README.md).

### Single Sign-On Integration Using Microsoft Entra ID (formerly Azure Active Directory)

#### Prerequisites

1. Configured and working Microsoft Entra ID:
    - preconfigured and working SSO for other applications
    - two new groups - one for `erag-admins`, one for `erag-users` - save `Object ID` for these entitites
    - defined user accounts that can be later added to either `erag-admins` or `erag-users` groups 
2. Registered a new Azure `App registration`:
    - configured with Redirect URI `https://auth.erag.com/realms/EnterpriseRAG/broker/oidc/endpoint`
    - in App registration -> Overview - save the `Application (client) ID` value
    - in App registration -> Overview -> Endpoints - save `OpenID Connect metadata document` value
    - in App registration -> Manage -> Certificates & secrets -> New client secret - create and save `Client secret` value
3. Add users to the newly created groups, either `erag-admins` or `erag-users` in Microsoft Entra ID

#### Keycloak Configuration via Ansible

To automatically configure Keycloak during deployment to use SSO configue the following settings in `deployment/inventory/**/config.yaml`

```yaml
keycloak:
  oidc:
    endpoint: ""
    alias: ""
    client_id: ""
    client_secret: ""
    admin_gid: ""
    user_gid: ""
```

`admin_gid` and `user_gid` fields are optional - you can configure them later if you do not want to use hardcoded groups.

#### Keycloak Configuration via Keycloak Web-GUI

To configure Enterprise RAG SSO using Azure Single Sign-On, follow these steps:

1. Log in as `admin` user into Keycloak and select the `EnterpriseRAG` realm.
2. Choose `Identity providers` from the left menu.
3. Add a new `OpenID Connect Identity Provider` and configure:
     - Field `Alias` - enter your SSO alias, for example `enterprise-sso`
     - Field `Display name` - enter your link display name to redirect to external SSO, for example `Enterprise SSO`
     - Field `Discovery endpoint` - enter your `OpenID Connect metadata document`. Configuration fields should autopopulate
4. Choose `Groups` in the left menu. Then create the following groups:
     1. `erag-admin-group` should consist of the following groups from Keycloak:
          - `(EnterpriseRAG-oidc) ERAG-admin`
          - `(EnterpriseRAG-oidc-backend) ERAG-admin`
          - `(EnterpriseRAG-oidc-minio) consoleAdmin` # if using internal MinIO
     2. `erag-user-group` should consist of the following groups from Keycloak:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-minio) readonly` # if using internal MinIO
5. Configure two `Identity mappers` in `Mappers` under the created `Identity provider`:
     1. Add Identity Provider Mapper - for group `erag-admin-group`:
          - Field `Name` - this is the `Object ID` from `erag-admins` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-admin-group`
     2. Add Identity Provider Mapper - for group `erag-user-group`:
          - Field `Name` - this is the `Object ID` from `erag-users` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-user-group`

After this configuration, the Keycloak login page should have an additional link at the bottom of the login form - named `Enterprise SSO`. This should redirect you to the Azure login page.

Depending on users' group membership in Microsoft Entra ID (either `erag-admins` or `erag-users`), users will have appropriate permissions mapped. For example, `erag-admins` will have access to the admin panel.

### Backup Functionality with VMWare Velero

Backup functionality has been added to Enterprise RAG to offer protection and reduce downtime in case of accidents.

This feature is currently disabled by default - due to certain configuration and maintenance effort that is related to this.

Recommended way to enable this feature is to plan for it up-front before deploying Kubernetes cluster as certain prerequisites need to be met.

> **Note**:<br>
> Backup functionality works on both single- and multi-node deployments. It does however need a suitable `StorageClass` supporting volume snapshots which might be provided by NFS server. That does not mandate multi-node setup.

#### Velero Prerequisites

To have a working backup and restore functionality the following items need to be ensured:

- Installation of a `StorageClass` with support for volume snapshots.<br>
  Velero works with volumes provisioned with a dedicated `StorageClass`, supporting volume snapshot.
  The [default solution](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/tree/main?tab=readme-ov-file#software-prerequisites) mentioned in documentation doesn't offer that.<br>
  Good choice for evaluation might be an installation of NFS server and storage driver in cluster. Simplified approach to achieve this in cluster is offered by `infrastructure.yaml` infrastructure Ansible playbook.
  At minimum the following values need to be set in cluster `config.yaml` to ensure this before starting infrastructure Ansible playbook:
  ```yaml
  install_csi: nfs
  ```
  See [Simplified Cluster Deployment procedure](../README.md#simplified-kubernetes-cluster-deployment) for details.

- Installation of VMWare Velero
  Velero can be installed externally or by use of `infrastructure.yaml` infrastructure Ansible playbook.<br>
  To ensure that velero is installed during deployment of cluster update `config.yaml` to have at least these parameters set accordingly:
  ```yaml
  velero:
    enabled: true
    namespace: velero

    velero_pod_labels:
      app.kubernetes.io/instance: velero
      app.kubernetes.io/name: velero

    install_server: true
    install_client: true
  ```
  Please review *sample* cluster config file comments for details.
  > **Note**:
  > Velero installation requires a valid `StorageClass` to be set up as default in cluster. Furthermore it needs support for volume snapshots, like the NFS storage driver offered by infrastructure Ansible playbook.

- Ensure suitable object storage for backups.<br>
  Backup functionality is installed with a basic instance of Minio object storage.<br>
  It might be necessary to adjust Minio settings to make sure it meets specific requirements.

#### Backup and Restore Configuration Variants

  - Custom `StorageClass`<br>
    Different storage driver may be configured in cluster to still support backup and restore.
    > **Note**:
    > `StorageClass` of choice must be consistently used for provisioning of new persistent volumes; it translates to making it the default StorageClass.

    > **Note**:
    > `LocalPath` provisioner as well as host-path based solutions won't work. They do not support volume snapshots.
    See [Velero documentation on Container Storage Interface](https://velero.io/docs/csi/) for details.
  - Custom installed NFS CSI storage driver for evaluation<br>
    To evaluate backup you may try NFS CSI storage driver mentioned in document [evaluation_of_backup](../docs/evaluation_of_backup.md). Please note that it might not meet production needs in the long run.
  - Externally installed Velero solution<br>
    To support standalone installation of Velero cluster deployment may skip installation of server. This requires following modification of cluster `config.yaml`:
    ```yaml
    velero:
      enabled: true
      namespace: VELERO_NAMESPACE

      # update as needed to allow Velero instance to be located during backup and restore operations
      velero_pod_labels:
        app.kubernetes.io/instance: velero
        app.kubernetes.io/name: velero

      install_server: false
      # ensure that client binary will be installed
      install_client: true
    ```
    This will support external instance of Velero.
  - Deployment of Velero server after cluster has already been set up<br>
    - Update the cluster `config.yaml` as explained in [Velero Prerequisites](#velero-prerequisites).
    - Start a post-installation configuration process with infrastructure Ansible playbook:
      ```shell
      ansible-playbook playbooks/infrastructure.yaml --tags post-install -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml -e deploy_k8s=false
      ```
    - Velero server and client will be installed, enabling the backup and restore operations.
  - Install externally a Velero client<br>
    Review [velero release](https://github.com/vmware-tanzu/velero/releases/tag/v1.16.1) for installation of Velero binary if not installed during cluster deployment.

#### Full Backup of User Data

This paragraph describes steps that are necessary to secure data coming from user. These include:
- ingested vector data,
- ingested documents,
- user accounts and credentials,
- chat history.

Backup operation is now directly supported with invocation of a dedicated `backup.yaml` ansible playbook.<br>
Backup can now be requested with the following command:
```shell
ansible-playbook playbooks/backup.yaml --tags backup,monitor_backup -e @inventory/test-cluster/config.yaml
```

Backup process will now start and will be monitored until completion (tag `monitor_backup` is optional).
As a result a `backup` object will be created in specified backup namespace (review `config.yaml`) that can be described with `kubectl`:
```shell
# list backup resources
kubectl get backup -n velero
NAME                     AGE
backup-20250803t050646   21h
backup-20250803t051937   21h
backup-20250804t010158   86m

# describe a backup resource to view details
kubectl describe backup backup-20250804t010158 -n velero
Name:         backup-20250804t010158
Namespace:    backup
# (details omitted for clarity)
Status:
  Backup Item Operations Attempted:  7
  Backup Item Operations Completed:  7
  Completion Timestamp:              2025-08-03T23:02:48Z
  Csi Volume Snapshots Attempted:    7
  Csi Volume Snapshots Completed:    7
  Expiration:                        2025-09-02T23:02:05Z
  Format Version:                    1.1.0
  Hook Status:
  Phase:  Completed
  Progress:
    Items Backed Up:  452
    Total Items:      452

```

Details can also be viewed with `velero` command:
```shell
velero backup describe backup-20250804t010158 --details
```

> **Note**: The name of the backup resource must be unique.<br>
> That's why the backup resource names are generated by `backup` playbook, according to pattern:<br>
> `(BACKUP_RESOURCE_PREFIX)-(TIMESTAMP)`, where:<br>
> - `BACKUP_RESOURCE_PREFIX` is the `config.yaml` setting `velero.backup.prefix`,
> - `TIMESTAMP` is a compact time and date representation.

#### Full Restore of User Data

This paragraph describes steps that are necessary to restore data from full backup created in previous step.

* Restore operation is now directly supported with invocation of a dedicated `backup.yaml` ansible playbook.<br>
* Restore can now be requested with the following command:
  ```shell
  ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore -e @inventory/test-cluster/config.yaml
  ```

* Restore process will now start and will be monitored until completion (tag `monitor_restore` is optional).
  A `backup` resource to restore will be the most recently completed backup resource. Furthermore the backup resource can be filtered by matching kubernetes resource labels specified in `config.yaml` for backup resource.

* To select a specific backup to restore from (not necessarily most recent) the following command may be used:
  ```shell
  ansible-playbook playbooks/backup.yaml --tags restore,monitor_restore -e @inventory/test-cluster/config.yaml -e '{"velero": {"restore_from": BACKUP_RESOURCE_ID} }'

  ```
  where `BACKUP_RESOURCE_ID` is the name of kubernetes `backup` resource to restore from.

* As a result a `restore` object will be created in specified backup namespace (review `config.yaml`) that can be described with `kubectl`:
  ```shell
  # list restore resources
  kubectl get restore -n velero
  NAME                      AGE
  restore-20250803t052410   21h
  restore-20250803t053604   21h
  restore-20250803t054219   21h

  # describe a restore resource to view details
  kubectl describe restore restore-20250803t053604 -n velero
  Name:         restore-20250803t053604
  Namespace:    backup
  Labels:       restore-reason=recovery
  # (details omitted for clarity)
  Status:
    Completion Timestamp:  2025-08-03T03:36:44Z
    Hook Status:
    Phase:  Completed
    Progress:
      Items Restored:  378
      Total Items:     378
  ```

* Details can also be viewed with `velero` command:
  ```shell
  velero restore describe restore-20250803t053604
  ```

* To gather further details you need to expose `minio` service locally.<br>
  Forward minio port 9000:
  ```bash
  # it's probably better to start this in a separate terminal
  kubectl port-forward --namespace velero svc/velero-minio 9000:9000
  ```
  And add an alias for `velero-minio.velero.svc` to `/etc/hosts`:
  ```bash
  # /etc/hosts
  127.0.0.1 localhost velero-minio.velero.svc
  ```

  Then call velero to review details:
  ```bash
  velero backup describe backup-20250803t051937 --details
  ```

* > **Note**
  >
  > Restore operation requires multiple tasks to be performed.<br>
  > Specifically the deploments hosting the user data need to be **removed** before being restored from saved objects and stored volume snapshots.
  >
  > This results in a period of unavailability of services, including but not limited to:
  > - authorization services (Keycloak instance),
  > - data ingestion pipelines (`edp` namespace).

  For better overview of the operation the monitoring mode is supported with optional ansible tag `monitor_restore`.<br>
  The monitor process won't finish until both restore process on Velero side and microservices pods have recovered.

* > **Note**
  >
  > When planning to use backup and restore it's recommended to make a copy of `ansible-logs` folder from original deployment. It might be necessary to properly set up credentials for services such as *fingerprint*, *chat history* and *edp* and restore them from backup. <br>
  > In case it's necessary to uninstall deployment to retry installation and restore from backup, folder should be restored before starting recovery install of ERAG again.

#### Removal of Velero from Cluster

  > **Note**: Either of the following approaches to removing velero will result in removal of backup and restore objects created with use of the velero.

* Normally velero will be removed along with cluster deletion:
  ```sh
  ansible-playbook -K playbooks/infrastructure.yaml --tags delete -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml
  ```

* Removing only the installed instance of velero without deleting the cluster:
  ```shell
  ansible-playbook playbooks/infrastructure.yaml --tags velero-delete -i inventory/test-cluster/inventory.ini -e @inventory/test-cluster/config.yaml -e deploy_k8s=false
  ```

#### Backup Links

- [Kubernetes CSI Documentation](https://kubernetes-csi.github.io/docs/)
- [Velero documentation](https://velero.io/docs/)


### Additional Pipelines

#### Language Translation Pipeline

> [!NOTE] ⚠️ **Preview Status – not integrated into UI**  
> This is a preview pipeline and is currently in active development. While core functionality is in place, it is not yet integrated into the RAG UI, and development and validation efforts are still ongoing.

This pipeline provides language translation capabilities using advanced Language Models from the ALMA family, where:

- ALMA-7B-R model - recommended for CPU-based execution
- ALMA-13B-R model - recomended for Gaudi-based (Habana) acceleration

To test the translation pipeline, first deploy it by following the instructions in [Deployment Options → Installation](#installation), using a configuration file based on [inventory/sample/config_language_translation.yaml](inventory/sample/config_language_translation.yaml).

Once deployed, run the provided shell script:
```bash
./scripts/test_translation.sh
```