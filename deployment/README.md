# Enterprise RAG solution
## Prerequisites

- Access to a Kubernetes v1.29 cluster 
- K8s cluster needs to have CSI-driver installed [local-path-provisioner](https://github.com/rancher/local-path-provisioner) with  `local_path_provisioner_claim_root: set to /mnt`. Example instruction how to set up K8s via Kubespray is here: [how_to_install_k8s_via_kubespray](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.x/docs/install_kubernetes.md)
- Ubuntu 22.04
- Verify if your setup is using valid software stack for Gaudi accelerators [Gaudi support matrix](https://docs.habana.ai/en/latest/Support_Matrix/Support_Matrix.html). Running LLM on CPU is possible but will reduce performance significantly.
- Prepared Gaudi node [prepare Gaudi node on K8s setup](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.x/deployment/microservices-connector/PREPARE_GAUDI.md)
- Make sure you have access granted to download and use chosen huggingface model. For example such access is mandatory in case of using  [mixtral-8x22B](https://huggingface.co/mistralai/Mixtral-8x22B-Instruct-v0.1).
- To ensure that telemetry works as expected `fs.inotify.max_user_instances` increased accordingly per node (Verified with 8192).

------------

### Quickstart with oneclick script

You can proceed through configuration, deployment and test connection using `one_click_chatqna.sh`:

#### Usage
```
./one_click_chatqna.sh -g HUG_TOKEN -z GRAFANA_PASSWORD -a [AWS_ACCESS_KEY_ID] -s [AWS_SECRET_ACCESS_KEY] -r [REGION] [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d PIPELINE -t [TAG]
```
Proxy variables are optional.

###  Configure
The `configure.sh` script automates the setup process by installing necessary tools needed:

- `make`
- `docker`
- `golang` (version 1.22.1)
- `helm`
- `awscli`
- `zip`
- `jq`

#### Usage:
```
./configure.sh -g HUG_TOKEN -a [AWS_ACCESS_KEY_ID] -s [AWS_SECRET_ACCESS_KEY] -r [REGION] [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY]
```
Proxy variables are optional.
> [!NOTE]
> The images are stored on AWS to simplify deployment process. The images can be build directly from the source using `update_images.sh` script and pushed to user defined registry. In such case please modify paths to images in [values.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.x/deployment/microservices-connector/helm/values.yaml)


As the result of `configure.sh`, a `.env` file is created. To enable Go-related configurations, source the `.env` file:

```sh
source .env
```

This step is crucial to avoid errors such as "make: go: No such file or directory" in subsequent steps.

### Build
To build and push images from source, use the `update_images.sh` script. This script performs the following:
1. Build specified images from source.
2. Push built images to a specified registry.

#### Usage
Run `./update_images.sh --help` to get detail information.

```
Usage: ./update_images.sh [OPTIONS] [COMPONENTS...]
Options:
        --build: Build specified components.
        --push: Push specified components to the registry.
        --no-build: Don't build specified components. (latest specified will be used)
        --no-push: Don't push specified components to the registry. (latest specified will be used)
        --registry: Specify the registry (default is aws, use localhost to setup local registry at p5000).
Components available: (default as all)
         gmcManager embedding-usvc reranking-usvc torcheserve retriever-usvc llm-uservice in-guard
Example: ./update_images.sh --build --push --registry my-registry embedding-usvc reranking-usvc
```

### Install chat Q&A
To streamline the deployment process, use the `install_chatqna.sh` script.

- Configure-  set your huggingface token changing value inside `helm/values.yaml` tokens.hugToken or use script:

```
./set_values.sh -g $YOUR_HUGGING_TOKEN
```
> [!NOTE]
> Grafana POD will require access to internet do download plugin. In order to do that we need to setup proxy settings here:[grafana_proxy](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.x/telemetry/helm/values.yaml)

Execute defined pipeline defined in [config/samples](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.x/deployment/microservices-connector/config/samples/)

You can check available options by executing install_chatqna.sh --help
```
Usage: ./install_chatqna.sh [OPTIONS]
Options:
        --aws: Use aws registry.
        --grafana_password (REQUIRED with --telemetry): Initial password for grafana.
        --kind: Changes dns value for telemetry(kind is kube-dns based).
        --deploy <PIPELINE_NAME>: Start the deployment process (default).
        Pipelines available: gaudi_torch_guard,gaudi_torch,gaudi,switch_gaudi,switch_xeon,xeon_llm_guard,xeon_torch_llm_guard,xeon_torch,xeon
        --tag: Use specific tag for deployment.
        --test: Run a connection test.
        --telemetry: Start telemetry services.
        --ui: Start auth and ui services (requires deployment).
        -cd|--clear-deployment: Clear deployment services.
        -ct|--clear-telemetry: Clear telemetry services.
        -cu|--clear-ui: Clear auth and ui services.
        -ca|--clear-all: Clear the all services.
        --upgrade: Helm will install or upgrade charts.
        -h|--help: Display this help message.
Example: ./install_chatqna.sh --deploy gaudi_torch_guard
Example: ./install_chatqna.sh --aws --deploy gaudi_torch --telemetry --ui --grafana_password pleasechangeit
Example: ./install_chatqna.sh --deploy gaudi_torch_guard
Example: ./install_chatqna.sh --aws --deploy gaudi_torch --telemetry --ui --grafana_password pleasechangeit

```
Example command:
```
./install_chatqna.sh --deploy chatQnA_gaudi_torch_guard --auth --telemetry --ui
```

In the above case the run should end with having all pods defined in [chatQnA_gaudi_torch_guard.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/rls-v0.5.0/deployment/microservices-connector/config/samples/chatQnA_gaudi_torch.yaml) in running state.

### Test:
To verify the functionality of the Chat Q&A pipeline, run the `test_connecton.sh` script. It will execute a test query and display the response.

### Access UI from your local machine

To access UI please forward bellow ports when connecting to server:

```
    LocalForward 1234 localhost:1234
    LocalForward 4173 localhost:4173
    LocalForward 3000 localhost:3000
``` 

Next you can access Enterprise RAG UI by typing in web browser: `http://localhost:4173/` on your local machine.

