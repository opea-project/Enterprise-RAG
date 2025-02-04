# Deploy Intel&reg; AI for Enterprise RAG

## Verify System Status

Before proceeding with this guide, verify that the following output is displayed when running `kubectl get pods -A`. This output indicates that all necessary Kubernetes components are running and ready to use. If not, refer to the [prerequisites](../docs/prerequisites.md) guide to set up your system to run the example in this document.

The output should show a list of pods from various namespaces, including:

        - `kube-system`: Calico, Kube-apiserver, Kube-controller-manager, Kube-scheduler, DNS, and NodeLocalDNS
        - `habana-system`: Habana device plugin
        - `local-path-storage`: Local path provisioner

Run `kubectl get pods -A` to verify that the output looks similar to the one below:
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

## Configure the Environment
To prepare your environment for development and deployment, run the following command (Proxy commands are optional):
```bash
./configure.sh [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]
```

This command will configure various tools in your environment, including `Docker`, `Helm`, `make`, `zip`, and `jq`.
> [!NOTE]
> Before running the script, please be aware that it uses `sudo` privileges to install the mentioned packages and configure settings. Please use with caution, as this may overwrite existing configurations.

The script completes successfully with the confirmation: `All installations and configurations are complete`.

## Storage Class
Users can define their own CSI driver that will be used during deployment. StorageClass should support accessMode ReadWriteMany(RWX).

> [!WARNING]
If the driver does not support ReadWriteMany accessMode, and EnterpriseRAG is deployed on a multi-node cluster, we can expect pods to hang in `container creating` state for `tei-reranking` or `vllm`. The root cause is that those pods would be using the same PVC `model-volume-llm` and only one of the pods will be able to access it if pods are on different nodes. This issue can be worked around by defining another PVC entry in [values.yaml](./microservices-connector/helm/values.yaml) and use it in reranking manifest: [teirerank.yaml](./microservices-connector/config/manifests/teirerank.yaml) in volumes section. However we strongly recommend using a storageClass that supports ReadWriteMany accessMode.

We recommend setting `volumeBindingMode` to `WaitForFirstConsumer`

### Seting default storageClass
Prior to running EnterpriseRAG solution, make sure you have set the correct StorageClass as the default one. Storage classes can be listed as in the below command:

```bash
ubuntu@node1:~/applications.ai.enterprise-rag.enterprise-ai-solution/deployment$ kubectl get sc -A
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  12d
```
We can use the following command to set defined storageClass as default one:
```bash
kubectl patch storageclass <storage_class_name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
Also make sure the `pvc` section in [values.yaml](./microservices-connector/helm/values.yaml) matches your storageClass capabilities.

### Skipping Warm-up for vLLM Deployment
The `VLLM_SKIP_WARMUP` environment variable controls whether the model warm-up phase is skipped during initialization. To modify this setting, update the deployment configuration in: 
 - For vLLM running on Gaudi: [vllm/docker/.env.hpu](./../src/comps/llms/impl/model_server/vllm/docker/.env.hpu)
  - For vLLM running on CPU: [vllm/docker/.env.cpu](./../src/comps/llms/impl/model_server/vllm/docker/.env.cpu)

> [!NOTE]
By default, `VLLM_SKIP_WARMUP` is set to True on Gaudi to reduce startup time.


### Running solution on CPU

In case we want to deploy the solution on CPUs instead of using Gaudi nodes, we need to make sure we have sufficient resources for running the LLM model server such as VLLM or TGI. The default resources used for deploying system are defined in [pod_resources_allocation](./../docs/pod_resource_allocation.md/)


#### Running solution on reduced model server pod resources
> [!NOTE]
It is possible to reduce resources for model server if having issues with node capacity, however performance drop is expected in such case. Always make sure value of `OMP_NUM_THREADS` is equal to number of CPU-s assigned to the container.

##### Setting variables for vllm as a model server
Please reduce value of `OMP_NUM_THREADS` in  [vllm variables](./../src/comps/llms/impl/model_server/vllm/docker/.env.cpu) and reduce resources in [vllm_deployment](./microservices-connector/config/manifests/vllm.yaml)

#### Setting variables for tgi as a model server

Please reduce value of `OMP_NUM_THREADS` in [tgi variables](./../src/comps/llms/impl/model_server/tgi/docker/.env.cpu) and reduce resources in [tgi_deployment](./microservices-connector/config/manifests/vllm.yaml).

## Deployment Options
There are two ways to install ChatQnA using the Enterprise RAG solution:
1.  Quick start with a one click script
2.  Step-by-Step Installation

### Quick Start with One Click Script

With the `one_click_chatqna.sh` script,  you can automate all the steps performed above such as configuration, building and pushing images and finally installing ChatQnA.

####  Install ChatQnA via `one_click_chatqna.sh`
Use the command below to install via the one click script:

```bash
./one_click_chatqna.sh -g HUG_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d [PIPELINE] -t [TAG] -y [REGISTRY] [--features FEATURES]
```
> [!NOTE]
> Using the `one_click_chatqna.sh` is an alternatve option to the Step-by-Step Installation described in the next section.

You can run `one_click_chatqna.sh --help` to get detailed information.

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
> You can build individual images, for example `./update_images.sh --build  embedding-usvc reranking-usvc` which only builds the embedding and reranking images.

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

If using EDP, update the `deployment/edp/values.yaml` file to increase the storage size under the `persistence` section. For example, set `size: 100Gi` to allocate 100Gi of storage. 

Similarly, for the selected Vector Store (for example `deployment/microservices-connector/manifests/redis-vector-db.yaml` manifest), you can increase the storage size under the PVC listing for `vector-store-data` PVC located in `deployment/microservices-connector/helm/values.yaml`. For example, set `size: 100Gi` to allocate 100Gi of storage for VectorStore database data.

> [!NOTE]
> The Vector Store storage should have more storage than file storage due to containing both extracted text and vector embeddings for that data.

##### Configure
The `set_values.sh` script automates Helm value configuration for the `microservices-connector` chart,
simplifying customization. Use the following to set your HF token to for services such as LLM, Embedding, Re-ranking:

```bash
./set_values.sh -p [HTTP_PROXY] -u [HTTPS_PROXY] -n [NO_PROXY] -g [HUGGINGFACEHUB_API_TOKEN] -r [REPOSITORY] -t [TAG]
```

The HF access token can be created [here](https://huggingface.co/settings/tokens).

Run the following command to deploy the `gaudi_torch_in_out_guards` pipeline, along with telemetry and UI services:

```bash
./install_chatqna.sh --deploy gaudi_torch_in_out_guards --auth --telemetry --ui
```

You can run `./install_chatqna.sh --help` to get detailed information.

Proceed to [Verify Services](#verify-services) to check if the deployment is successful.

## Verify Services

Run `kubectl get pods -A` to verify that the output looks as below:
```
NAMESPACE            NAME                                                       READY   STATUS    RESTARTS      AGE
auth-apisix          auth-apisix-54ffcf8d66-x6bx5                               1/1     Running   0             36m
auth-apisix          auth-apisix-etcd-0                                         1/1     Running   0             36m
auth-apisix          auth-apisix-ingress-controller-6b9c4bffbb-ndb6f            1/1     Running   0             36m
auth                 keycloak-0                                                 1/1     Running   0             38m
auth                 keycloak-postgresql-0                                      1/1     Running   0             38m
chatqa               client-test-87d6c7d7b-rgqfb                                1/1     Running   0             16m
chatqa               embedding-svc-deployment-7d4f577884-rbq6h                  1/1     Running   0             34m
chatqa               input-scan-svc-deployment-54c55d57d4-4wgrb                 1/1     Running   0             34m
chatqa               llm-svc-deployment-6988978796-kt2bl                        1/1     Running   0             34m
chatqa               redis-vector-db-deployment-57484464cc-tbslv                1/1     Running   0             34m
chatqa               reranking-svc-deployment-bb66bccbd-ww7lf                   1/1     Running   0             34m
chatqa               retriever-svc-deployment-b6455474f-wqbbd                   1/1     Running   0             34m
chatqa               router-service-deployment-5b9fcd6d94-grjln                 1/1     Running   0             34m
chatqa               tei-reranking-svc-deployment-db55fbbc7-v5hfj               1/1     Running   0             34m
chatqa               vllm-gaudi-svc-deployment-7f8c68d8d4-nqnsm                 1/1     Running   0             34m
chatqa               torchserve-embedding-svc-deployment-5d66d585fd-bnkz6       1/1     Running   0             34m
dataprep             dataprep-svc-deployment-6bcdcbcbff-7cbp5                   1/1     Running   0             34m
dataprep             embedding-svc-deployment-f4f4d46cb-x6mbn                   1/1     Running   0             34m
dataprep             ingestion-svc-deployment-7c5567dc66-tlrpk                  1/1     Running   0             34m
dataprep             router-service-deployment-94b874cc8-8qb52                  1/1     Running   0             34m
dataprep             torchserve-embedding-svc-deployment-5d66d585fd-dxtqj       1/1     Running   0             34m
habana-system        habanalabs-device-plugin-daemonset-gjs67                   1/1     Running   0             43h
ingress-nginx        ingress-nginx-controller-548874d566-m6g2k                  1/1     Running   0             17m
kube-system          calico-kube-controllers-68485cbf9c-dr9vd                   1/1     Running   0             44h
kube-system          calico-node-gnxk9                                          1/1     Running   0             44h
kube-system          coredns-69db55dd76-4zq74                                   1/1     Running   0             44h
kube-system          dns-autoscaler-6d5984c657-b7724                            1/1     Running   0             44h
kube-system          kube-apiserver-node1                                       1/1     Running   1             44h
kube-system          kube-controller-manager-node1                              1/1     Running   2             44h
kube-system          kube-proxy-qt4c4                                           1/1     Running   0             44h
kube-system          kube-scheduler-node1                                       1/1     Running   1             44h
kube-system          nodelocaldns-nltqf                                         1/1     Running   0             44h
local-path-storage   local-path-provisioner-f78b6cbbc-4hfs9                     1/1     Running   0             95m
monitoring-traces    otelcol-traces-collector-7f85cbcdfd-5w5q8                  1/1     Running   0             17m
monitoring-traces    telemetry-traces-minio-9c6df94cb-s6fdr                     1/1     Running   0             18m
monitoring-traces    telemetry-traces-otel-operator-bb746c85f-z9dsr             2/2     Running   0             18m
monitoring-traces    telemetry-traces-tempo-compactor-5454fbb6b7-sn98c          1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-distributor-7cb5fbf47c-98rjp        1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-gateway-75c6965c96-nfrz2            1/1     Running   0             18m
monitoring-traces    telemetry-traces-tempo-ingester-0                          1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-ingester-1                          1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-ingester-2                          1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-memcached-0                         1/1     Running   0             18m
monitoring-traces    telemetry-traces-tempo-metrics-generator-66d7d94c7-q9pt7   1/1     Running   3 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-querier-668bbcf578-smx96            1/1     Running   2 (18m ago)   18m
monitoring-traces    telemetry-traces-tempo-query-frontend-5cf5f78678-lqkpg     1/1     Running   3 (18m ago)   18m
monitoring           alertmanager-telemetry-kube-prometheus-alertmanager-0      2/2     Running   0             20m
monitoring           habana-metric-exporter-ds-hxhx4                            1/1     Running   0             21m
monitoring           loki-backend-0                                             2/2     Running   0             20m
monitoring           loki-canary-jxj57                                          1/1     Running   0             20m
monitoring           loki-read-675bd78669-c4rmq                                 1/1     Running   0             20m
monitoring           loki-write-0                                               1/1     Running   0             20m
monitoring           prometheus-telemetry-kube-prometheus-prometheus-0          2/2     Running   0             20m
monitoring           telemetry-grafana-574d7c8946-976pl                         3/3     Running   0             21m
monitoring           telemetry-kube-prometheus-operator-74644bf687-ndh87        1/1     Running   0             21m
monitoring           telemetry-kube-state-metrics-7486fd66d6-px9mg              1/1     Running   0             21m
monitoring           telemetry-logs-loki-chunks-cache-0                         2/2     Running   0             20m
monitoring           telemetry-logs-loki-results-cache-0                        2/2     Running   0             20m
monitoring           telemetry-logs-minio-0                                     1/1     Running   0             20m
monitoring           telemetry-logs-otelcol-logs-agent-8t5zl                    1/1     Running   0             20m
monitoring           telemetry-prometheus-node-exporter-kc624                   1/1     Running   0             21m
monitoring           telemetry-prometheus-redis-exporter-6c8448f67b-g9f5t       1/1     Running   0             21m
rag-ui               fingerprint-usvc-686c599cbf-qc567                          1/1     Running   0             16m
rag-ui               mongodb-8474b8bc56-5nsnl                                   1/1     Running   0             16m
rag-ui               ui-chart-79685cc99f-wb9nd                                  1/1     Running   0             16m
system               gmc-contoller-7fd7cf64-tcq9p                               1/1     Running   0             34m
------------------------------------------------------------
```

## Available Pipelines

This [page](./microservices-connector/config/samples) contains a collection of sample pipeline configurations, which can be easily deployed using the 
`install_chatqna.sh` script.

Explore a diverse set of easily deployable sample pipeline configurations. Examples include:

- `Multilingual Pipeline`: A multilingual pipeline designed to detect the language of the user's query and the response generated by the initial LLM. It dynamically configures a prompt to translate the generated response back into the language of the user's query, ensuring seamless multilingual communication.

- `Input and Output Guard Pipeline`: Adds layers of protection by scanning both incoming queries and outgoing responses to ensure security and compliance.


## Interact with ChatQnA

### Test Deployment

To verify that the deployment was successful, run the following command:
```bash
./test_connection.sh
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

### Access the UI

To access the cluster, please update the `/etc/hosts` file on your machine to match the domain name with the externally
exposed IP address of the cluster.

For example, the updated file content should resemble the following:

```
<Ingress external IP> erag.com grafana.erag.com auth.erag.com s3.erag.com minio.erag.com
```

> [!NOTE]
> This is the IPv4 address of local machine.

On a Windows machine, this file is typically located at `C:\Windows\System32\drivers\etc\hosts`.

Once the update is complete, you can access the Enterprise RAG UI by typing the following URL in your web browser:
`https://erag.com`

Keyclock can be accessed via:
`https://auth.erag.com`

Grafana can be accessed via:
`https://grafana.erag.com`

MinIO Console can be accessed via:
`https://minio.erag.com`

S3 API is exposed at:
`https://s3.erag.com`

### UI credentials for the first login

Once deployment is complete, there will be file `default_credentials.txt` created in `deployment` folder with one time passowrds for application admin and user. After one time password will be provided you will be requested to change the default password.

> [!CAUTION]
> Please remove file `default_credentials.txt` after the first succesfull login.

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

## Clear Deployment
Run this command to delete all namespaces, custom resource definitions, releases, and services associated with the ChatQNA pipeline:
```bash
./install_chatqna.sh -ca
```

## Additional features

### Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)

For deploying ChatQnA components with Intel® Trust Domain Extensions (Intel® TDX), refer to the [Running Enterprise RAG with Intel® Trust Domain Extensions (Intel® TDX)](../docs/tdx.md) guide.

> [!NOTE]
> Intel TDX feature in Enterprise RAG is experimental.
