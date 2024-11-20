# Deploy Intel(R) AI for Enterprise RAG

### Verify System Status

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
>**Note**: Before running the script, please be aware that it uses `sudo` privileges to install the mentioned packages and configure settings. **Please use with caution**, as this may overwrite existing configurations.

The script completes successfully with the confirmation: `All installations and configurations are complete`.

## Deployment Options
There are two ways to install ChatQnA using the Enterprise RAG solution:
1.  Step-by-Step Installation
2.  Quick start with a one click script

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
>**Note**: The `--build` argument builds all the images. 
>You can build individual images, for example `./update_images.sh --build  embedding-usvc reranking-usvc` which only builds the embedding and reranking images

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

>**Note**: Multiple steps can also be executed in a single step using `./update_images.sh --build --setup-registry --push`, which simplifies the build process and reduces the number of commands needed.

Run `./update_images.sh --help` to get detailed information.

####  Install ChatQnA via `install_chatqna.sh`

To install ChatQnA, use the `install_chatqna.sh` script, a streamlined deployment process for our 
Enterprise RAG solution. This script automates the setup of ChatQnA services, including pipeline 
deployment, telemetry integration, and UI authentication.

##### Configure 
The `set_values.sh` script automates Helm value configuration for the `microservices-connector` chart, 
simplifying customization. Use the following to set your HF token to for services such as LLM, Embedding, Re-ranking: 

```bash
./set_values.sh -g HUGGINGFACEHUB_API_TOKEN [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]
```

The HF access token can be created [here](https://huggingface.co/settings/tokens).

Run the following command to deploy the `gaudi_torch_in_out_guards` pipeline, along with telemetry and UI services:

```bash
./install_chatqna.sh --deploy gaudi_torch_in_out_guards --auth --telemetry --ui --ip 10.211.187.74 --grafana_password mypassword 
```
>**Note:**  The IP address `10.211.187.74` is being exposed to the outside world from within a private network segment, allowing external access to the ChatQnA deployment.

You can run `./install_chatqna.sh --help` to get detailed information.

Proceed to [Verify Services](#verify-services) to check if the deployment is successful.

### Quick Start with One Click Script

With the `one_click_chatqna.sh` script,  you can automate all the steps performed above such as configuration, building and pushing images and finally installing ChatQnA. 

####  Install ChatQnA via `one_click_chatqna.sh`
Use the command below to install via the one click script:

```bash
./one_click_chatqna.sh -g HUGGINGFACEHUB_API_TOKEN -z GRAFANA_PASSWORD [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d PIPELINE -t [TAG] -i [IP]
```
>**Note:** Using the `one_click_chatqna.sh` is an alternatve option to the Step-by-Step Installation described in the previous section.

You can run `one_click_chatqna.sh --help` to get detailed information.

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
chatqa               tgi-gaudi-svc-deployment-7f8c68d8d4-nqnsm                  1/1     Running   0             34m
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
<Ingress external IP> erag.com grafana.erag.com auth.erag.com
```
>**Note:** This is the IPv4 address of local machine

On a Windows machine, this file is typically located at `C:\Windows\System32\drivers\etc\hosts`.

Once the update is complete, you can access the Enterprise RAG UI by typing the following URL in your web browser:
`https://erag.com`

Keyclock can be accessed via:
`https://auth.erag.com`

Grafana can be accessed via:
`https://grafana.erag.com`

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
