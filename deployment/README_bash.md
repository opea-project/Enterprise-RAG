> [!IMPORTANT]  
> ⚠️ **Warning:** Deployment via bash scripts is **deprecated** and will be **removed in a future release**.  
> It is strongly recommended to use the [Ansible deployment method](./README.md) instead.

# Deploy Intel&reg; AI for Enterprise RAG

This document details the deployment of Intel® AI for Enterprise RAG. By default, the guide assumes a Xeon + Gaudi deployment. If you are deploying on Xeon-only hardware, please follow the Xeon-only instructions marked throughout this guide.

## Table of Contents

 1. [Verify System Status](#verify-system-status)
 2. [Configure the Environment](#configure-the-environment)
 3. [Storage Class](#storage-class)
 4. [Defining Resource for you machine](#defining-resource-for-you-machine)
 5. [Deployment Options](#deployment-options)
    1.  [Quick start with a one click script](#quick-start-with-one-click-script)
    2.  [Step-by-Step Installation](#build-step-by-step)
 6. [Verify Services](#verify-services)
 7. [Available Pipelines](#available-pipelines)
 8. [Interact with ChatQnA](#interact-with-chatqna)
     1. [Test Deployment](#test-deployment)
     2. [Access UI/Grafana](#access-the-uigrafana)
 9. [Configure ChatQnA](#configure-chatqna)
 10. [Clear Deployment](#clear-all)
 11. [Additional features](#additional-features)
     1. [Enabling Pod Security Admission (PSA)](#enabling-pod-security-admission-psa)
     2. [Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)](#running-enterprise-rag-with-intel-trust-domain-extensions-intel-tdx)
     3. [Single Sign On Integration using Microsoft Entra ID (formerly Azure Active Directory)](#single-sign-on-integration-using-microsoft-entra-id-formerly-azure-active-directory)
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

## Configure the Environment
To prepare your environment for development and deployment, run the following command (Proxy commands are optional):
```bash
./configure.sh [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]
```

This command will configure various tools in your environment, including `Docker`, `Helm`, `make`, `zip`, and `jq`.
> [!NOTE]
> Before running the script, please be aware that it uses `sudo` privileges to install the mentioned packages and configure settings. Please use with caution, as this may overwrite existing configurations.

> [!NOTE]
> ./configure.sh installs Docker. It might not start the docker process. If it is your case, run `systemctl start docker`. To check if docker is running, run `systemctl status docker`.

The script completes successfully with the confirmation: `All installations and configurations are complete`.

## Storage Class
Users can define their own CSI driver that will be used during deployment. StorageClass should support accessMode ReadWriteMany(RWX).

> [!WARNING]
If the driver does not support ReadWriteMany accessMode, and EnterpriseRAG is deployed on a multi-node cluster, we can expect pods to hang in `container creating` state for `tei-reranking` or `vllm`. The root cause is that those pods would be using the same PVC `model-volume-llm` and only one of the pods will be able to access it if pods are on different nodes. This issue can be worked around by defining another PVC entry in [values.yaml](./components/gmc/microservices-connector/helm/values.yaml) and use it in reranking manifest: [teirerank.yaml](./components/gmc/microservices-connector/config/manifests/teirerank.yaml) in volumes section. However we strongly recommend using a storageClass that supports ReadWriteMany accessMode.

We recommend setting `volumeBindingMode` to `WaitForFirstConsumer`

### Setting Default Storage Class
Before running the EnterpriseRAG solution, ensure that you have set the correct StorageClass as the default one. You can list storage classes using the following command:

```bash
ubuntu@node1:~/applications.ai.enterprise-rag.enterprise-ai-solution/deployment$ kubectl get sc -A
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  12d
```

To set a specific storage class as the default, use the following command:
```bash
kubectl patch storageclass <storage_class_name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
Additionally, ensure that the `pvc` section in [values.yaml](./components/gmc/microservices-connector/helm/values.yaml) matches your chosen storage class's capabilities.

## Defining Resource for you machine

The default resource allocations are defined for Xeon only deployment in [`resources-reference-cpu.yaml`](./pipelines/chatqa/resources-reference-cpu.yaml) or for Xeon + Gaudi in [`resources-reference-hpu.yaml`](./pipelines/chatqa/resources-reference-hpu.yaml).

> [!NOTE]
It is possible to reduce the resources allocated to the model server if you encounter issues with node capacity, but this will likely result in a performance drop. Recommended Hardware parameters to run RAG pipeline are available [here](../README.md#hardware-prerequisites-for-deployment-using-xeon-only).

> [!NOTE]
EnterpriseRAG allows to implement autoscaling mechanism for pods. For more information how to fill `hpa` section reffer to [horizontal pod autoscaler](#enabling-horizontal-pod-autoscaling)

For Enhanced Dataprep Pipeline (EDP) configuration, please refer to a separate helm chart located in `deployment/components/edp` folder. It does not have a separate `resources*.yaml` definition. To change resources before deployment, locate the [`values.yaml`](./components/edp/values.yaml) file and edit definition for particular elements from that deployment.

### Skipping Warm-up for vLLM Deployment
The `VLLM_SKIP_WARMUP` environment variable controls whether the model warm-up phase is skipped during initialization. To modify this setting, update the deployment configuration in:
  - For vLLM running on Gaudi: [vllm/docker/.env.hpu](./../src/comps/llms/impl/model_server/vllm/docker/.env.hpu)
  - For vLLM running on CPU: [vllm/docker/.env.cpu](./../src/comps/llms/impl/model_server/vllm/docker/.env.cpu)

> [!NOTE]
By default, `VLLM_SKIP_WARMUP` is set to True on Gaudi to reduce startup time.

### additional settings for running telemetry

Enterprise RAG includes the installation of a telemetry stack by default, which requires setting the number of iwatch open descriptors on each cluster host. For more information, follow the instructions in [Number of iwatch open descriptors](./components/telemetry/helm/charts/logs/README.md#1b-number-of-iwatch-open-descriptors)

## Deployment Options
There are two ways to install ChatQnA using the Enterprise RAG solution:
1.  [Quick start with a one click script](#quick-start-with-one-click-script)
2.  [Step-by-Step Installation](#build-step-by-step)

### Quick Start with One Click Script

With the `one_click_chatqna.sh` script,  you can automate all the steps performed above such as configuration, building and pushing images and finally installing ChatQnA.

####  Install ChatQnA via `one_click_chatqna.sh`
Use the command below to install via the one click script:

##### Xeon + Gaudi (Default)
```bash
./one_click_chatqna.sh -g HUG_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY_NAME] [-r REGISTRY_PATH] [--features FEATURES]
```

##### Xeon-Only
```bash
./one_click_chatqna.sh -g HUG_TOKEN -d reference-cpu.yaml [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -t [TAG] -y [REGISTRY_NAME] [-r REGISTRY_PATH] [--features FEATURES]
```

> [!NOTE]
> For Xeon-only pass `reference-cpu.yaml` as shown above.
>
> Using the `one_click_chatqna.sh` is an alternative option to the Step-by-Step Installation described in the next section.

You can run `./one_click_chatqna.sh --help` to get detailed information.

Proceed to [Verify Services](#verify-services) to check if the deployment is successful.

### Build Step-by-Step

#### Build and Push Images
Enterprise RAG is built on top of a collection of microservice components that form a service-based toolkit. This includes a variety of services such as llm (large language models), embedding, and reranking, among others.

The `update_images.sh` script is responsible for building the images for these microservices from source
and pushing them to a specified registry. The script consists of three main steps:

##### Step 1: Build

The first step is to build the images for each microservice component using the source code. This involves
compiling the code, packaging it into Docker images, and performing any necessary setup tasks.

```bash
./update_images.sh --build
```

> [!NOTE]
> - You can build individual images, for example `./update_images.sh --build  embedding-usvc reranking-usvc` which only builds the embedding and reranking images.
> - You can use `-j <number of concurrent tasks>` parameter to increase number of concurrent tasks.
> - List of available images is available, when running `./update_images.sh --help`.

##### Step 2: Setup Registry

The second step is to configure the registry where the built images will be pushed. This may involve
setting up authentication, specifying the image tags, and defining other configuration parameters.

```bash
./update_images.sh --setup-registry
```

##### Step 3: Push

The final step is to push the built images to the configured registry. This ensures that the images are
deployed to the desired environment and can be accessed by the application.

```bash
./update_images.sh --push
```
> [!NOTE]
> Multiple steps can also be executed in a single step using `./update_images.sh --build --setup-registry --push`, which simplifies the build process and reduces the number of commands needed.

Run `./update_images.sh --help` to get detailed information.

####  Install ChatQnA via `install_chatqna.sh`

To install ChatQnA, use the `install_chatqna.sh` script, a streamlined deployment process for our
Enterprise RAG solution. This script automates the setup of ChatQnA services, including pipeline
deployment, telemetry integration, and UI authentication.

##### Storage settings

> [!NOTE]
> The default settings are suitable for smaller deployments only (by default, approximately 5GB of data).

You can expand the storage configuration for both the Vector Store and MinIO deployments by modifying their respective configurations:

If using EDP, update the `deployment/components/edp/values.yaml` file to increase the storage size under the `persistence` section. For example, set `size: 100Gi` to allocate 100Gi of storage.

Similarly, for the selected Vector Store (for example `deployment/components/gmc/microservices-connector/config/manifests/redis-vector-db.yaml` manifest), you can increase the storage size under the PVC listing for `vector-store-data` PVC located in `deployment/components/gmc/microservices-connector/helm/values.yaml`. For example, set `size: 100Gi` to allocate 100Gi of storage for VectorStore database data.

> [!NOTE]
> The Vector Store storage should have more storage than file storage due to containing both extracted text and vector embeddings for that data.

##### Configure
The `set_values.sh` script automates Helm value configuration for the `deployment/components/gmc/microservices-connector/helm` chart,
simplifying customization. Use the following to set your HF token to for services such as LLM, Embedding, Re-ranking. Retrieve your HuggingFace Token [here](https://huggingface.co/settings/tokens).

> [!NOTE]
> The default LLM for Xeon execution is `meta-llama/Llama-3.1-8B-Instruct`. 
> Ensure your HUGGINGFACEHUB_API_TOKEN grants access to this model.
> Refer to the [official Hugging Face documentation](https://huggingface.co/docs/hub/models-gated) for instructions on accessing gated models.


```bash
./set_values.sh -p [HTTP_PROXY] -u [HTTPS_PROXY] -n [NO_PROXY] -g [HUGGINGFACEHUB_API_TOKEN] -r [REPOSITORY] -t [TAG]
```

The HF access token can be created [here](https://huggingface.co/settings/tokens).

##### Xeon + Gaudi (Default):

Run the following command to deploy the `reference-hpu.yaml` pipeline, along with telemetry and UI services:
```bash
./install_chatqna.sh --deploy reference-hpu.yaml --auth --telemetry --ui
```

You can run `./install_chatqna.sh --help` to get detailed information.

##### Xeon-Only:
This command is intended for Xeon-only deployments, deploying the `reference-cpu.yaml` pipeline along with telemetry and UI services:

```bash
./install_chatqna.sh --deploy reference-cpu.yaml --auth --telemetry --ui
```

You can run `./install_chatqna.sh --help` to get detailed information.

Proceed to [Verify Services](#verify-services) to check if the deployment is successful.


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
------------------------------------------------------------
</pre>
</details>

## Available Pipelines

This [page](./pipelines/chatqa/examples) contains a collection of sample pipeline configurations, which can be easily deployed using the
`install_chatqna.sh` script.

Explore a diverse set of easily deployable sample pipeline configurations. Examples include:

- `Input and Output Guard Pipeline`: Adds layers of protection by scanning both incoming queries and outgoing responses to ensure security and compliance.

> [!NOTE]
For Xeon + Gaudi deployments, set pipeline to `reference-hpu.yaml`, while for Xeon-only deployments use `reference-cpu.yaml`.

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
Test finished succesfully
```

### Access the UI/Grafana

To access the UI, do the following:
1. Forward the port from the ingress pod.
```bash
sudo -E kubectl port-forward --namespace ingress-nginx svc/ingress-nginx-controller 443:https
```
2. If you'd like to access the UI from another machine, tunel the port from the host:
```bash
ssh -L 443:localhost:443 user@ip
```
3. Update `/etc/hosts` file on the machine where you'd like to access the UI to match the domain name with the externally exposed IP address of the cluster. On a Windows machine, this file is typically located at `C:\Windows\System32\drivers\etc\hosts`.

     For example, the updated file content should resemble the following:

```bash
127.0.0.1 erag.com grafana.erag.com auth.erag.com s3.erag.com minio.erag.com
```

> [!NOTE]
> This is the IPv4 address of local machine.

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
> Before ingesting the data, access the `https://s3.erag.com` to agree to accessing the self-signed certificate.

### UI credentials for the first login

Once deployment is complete, there will be file `default_credentials.txt` created in `deployment` folder with one time passwords for application admin and user. After one time password will be provided you will be requested to change the default password.

> [!CAUTION]
> Please remove file `default_credentials.txt` after the first succesful login.

### Credentials for Grafana and Keycloak

Default credentials for Keycloak and Grafana:
- **username:** admin
- **password:** stored in `default_credentials.txt` file, please change passwords after first login in Grafana or Keycloak.

> [!CAUTION]
> Please remove file `default_credentials.txt` after the first succesfull login and changing passwords.

### Credentials for Vector Store

Default credentials for selected Vector Store are stored in `default_credentials.txt` and are generated on first deployment.

### Credentials for Enhanced Dataprep Pipeline (EDP)

Default credentials for Enhanced Dataprep services:

MinIO:
- For accessing MinIO either by API or Web-UI (MinIO Console), please use the user credentials for `erag-admin`.

Internal EDP services credentials:

Redis:
- **username:** default
- **password:** stored in `default_credentials.txt`

Postgres:
- **username:** edp
- **password:** stored in `default_credentials.txt`

### Data Ingestion, UI and Telemetry

For adding data to the knowledge base and exploring the UI interface visit [this](../docs/UI_features.md) page.

For accessing Grafana dashboards for all the services, visit [this](../docs/telemetry.md) page.

## Configure ChatQnA
To change the LLM model in the pipeline, follow the instructions [here](../docs/configure_pipeline.md)

It is also possible to configure the input and output guardrails for the LLM service. Follow instructions [here](../src/comps/guardrails/llm_guard_input_guardrail/README.md) for input guardrails and [here](../src/comps/guardrails/llm_guard_output_guardrail/README.md) for output guardrails.

## Clear All
Run this command to delete all namespaces, custom resource definitions, releases, and services associated with the ChatQNA pipeline:
```bash
./install_chatqna.sh -ca
```

## Additional features

### Enabling Horizontal pod autoscaling

The feature enables automated scaling mechanism for pipeline components that might become bottleneck for RAG pipeline. The components are being scaled up based on rules defined in `hpa` section [resources-reference-cpu.yaml](./pipelines/chatqa/resources-reference-cpu.yaml) when running on Xeon or [resources-reference-hpu.yaml](./pipelines/chatqa/resources-reference-hpu.yaml) when running on Gaudi.
To enable HPA use option `--hpa` when running the `install_chatqa.sh`. 
For more information how to set parameters in HPA section please refer to this [README](./components/hpa/README.md).

To update you HPA configuration:
- Modify `hpa` section in resources file
- Update configuration by running: `./install_chatqa.sh` command with `--upgrade` option
bash
```
./install_chatqna.sh --deploy <pipeline> --upgrade --no-edp --no-mesh --hpa
```
For detailed information how to configure pipeline please reffer to:
[configure_pipeline](./../docs/configure_pipeline.md)

### Enabling Pod Security Admission (PSA)
Pod Security Admission (PSA) is a built-in admission controller that enforces the Pod Security Standards (PSS). These standards define different isolation levels for pods to ensure security and compliance within a cluster. PSA operates at the namespace level and uses labels to enforce policies on pods when they are created or updated.

We can deploy enterprise RAG with enforced validation of PSS across all deployed namespaces. To enable PSS use option `--enable-pss` when running the `install_chatqa.sh` script. To find more information please refer to the [deploy](#install-chatqna-via-install_chatqnash) section in [Step-by-Step Approach](#build-step-by-step)

### Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

For deploying ChatQnA components with Intel® Trust Domain Extensions (Intel® TDX), refer to the [Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)](../docs/tdx.md) guide.

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.

### Single Sign On Integration using Microsoft Entra ID (formerly Azure Active Directory)

#### Prerequisites

1. Configured and working Microsoft Entra ID 
     - preconfigured and working SSO for other applications
     - two new groups - one for `erag-admins`, one for `erag-users` - save `Object ID` for those entitites
     - defined some user accounts that can be later added to either `erag-admins` or `erag-users` groups 
2. Registered a new Azure `App registration`
     - configured with Redirect URI `https://auth.erag.com/realms/EnterpriseRAG/broker/oidc/endpoint`
     - in App registration -> Overview - save the `Application (client) ID` value
     - in App registration -> Overview -> Endpoints - save `OpenID Connect metadata document` value
     - in App registration -> Manage -> Cerficiates & secrets -> New client secret - create and save `Client secret` value
3. Add users to newly created groups, either `erag-admins` or `erag-users` in Microsoft Entra ID

#### Keycloak configuration

To configure Enterprise RAG SSO using Azure Single Sign On use the following steps:

1. Log in as `admin` user into Keycloak and select `EnterpriseRAG` realm.
2. Choose `Identity providers` from the left menu.
3. Add a new `OpenID Connect Identity Provider` and configure:
     - Field `Alias` - enter your SSO alias, for example `enterprise-sso`
     - Field `Display name` - enter your link display name to redirect to external SSO, for example `Enterprise SSO`
     - Field `Discovery endpoint` - enter your `OpenID Connect metadata document`. Configuration fields should autopopulate
4. Choose `Groups` in left menu. Then create the following groups:
     1. `erag-admin-group` should consist of following groups from keycloak:
          - `(EnterpriseRAG-oidc) ERAG-admin`
          - `(EnterpriseRAG-oidc-backend) ERAG-admin`
          - `(EnterpriseRAG-oidc-minio) consoleAdmin` # if using internal MinIO
     2. `erag-user-group` should consist of following groups from keycloak:
          - `(EnterpriseRAG-oidc) ERAG-user`
          - `(EnterpriseRAG-oidc-backend) ERAG-user`
          - `(EnterpriseRAG-oidc-minio) readonly` # if using internal MinIO
5. Configure two `Identity mappers` in `Mappers` under created `Identity provider`
     1. Add Identity Provider Mapper - for group `erag-admin-group`
          - Field `Name` - this is the `Object ID` from `erag-admins` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-admin-group`
     2. Add Identity Provider Mapper - for group `erag-user-group`
          - Field `Name` - this is the `Object ID` from `erag-users` from Microsoft Entra ID
          - Field `Mapper type` - enter `Hardcoded Group`
          - Field `Group` - select `erag-user-group`

After this configuration, Keycloak log-in page should have an additional link on the bottom of the log-in form - named `Enterprise SSO`. This should redirect you to Azure log-in page.

Depending on users' group membership in Microsoft Entra ID (either `erag-admins` or `erag-users`) users will have appropriate permissions mapped. For example, `erag-admins` will have access to the admin panel.
