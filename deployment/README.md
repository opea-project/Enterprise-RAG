# Enterprise RAG solution
## Prerequisites
- **Kubernetes Cluster**: Access to a Kubernetes v1.29 cluster
 - **CSI Driver**: The K8s cluster must have the CSI driver installed, using the [local-path-provisioner](https://github.com/rancher/local-path-provisioner) with `local_path_provisioner_claim_root` set to `/mnt`. For an example of how to set up Kubernetes via Kubespray, refer to the guide: [How to Install Kubernetes via Kubespray](../docs/install_kubernetes.md).
 - **Operating System**: Ubuntu 22.04
 - **Gaudi Software Stack**: Verify that your setup uses a valid software stack for Gaudi accelerators, see [Gaudi support matrix](https://docs.habana.ai/en/latest/Support_Matrix/Support_Matrix.html). Note that running LLM on a CPU is possible but will significantly reduce performance.
 - **Prepared Gaudi Node**: Please refer to the [Prepare Gaudi Node on K8s Setup](./microservices-connector/PREPARE_GAUDI.md) guide.
 - **Hugging Face Model Access**: Ensure you have the necessary access to download and use the chosen Hugging Face model. For example, such access is mandatory when using the [Mixtral-8x22B](https://huggingface.co/mistralai/Mixtral-8x22B-Instruct-v0.1).

In addition, to ensure that telemetry works as expected `fs.inotify.max_user_instances` increased accordingly per node (verified with 8192).

------------

### Quickstart with oneclick script

You can proceed through configuration, deployment, and test connection using `one_click_chatqna.sh`:

#### Usage
```
./one_click_chatqna.sh -g HUG_TOKEN -z GRAFANA_PASSWORD -a [AWS_ACCESS_KEY_ID] -s [AWS_SECRET_ACCESS_KEY] -r [REGION] [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -d PIPELINE -t [TAG]
```
Proxy variables are optional.

###  Configure
The `configure.sh` script automates the setup process by installing the necessary tools:

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
> The images are stored on AWS to simplify the deployment process. The images can be built directly from the source using the `update_images.sh` script and pushed to user defined registry. In such case please modify paths to images in [values.yaml](./microservices-connector/helm/values.yaml)


As the result of `configure.sh`, a `.env` file is created. To enable Go-related configurations, source the `.env` file:

```sh
source .env
```

This step is crucial to avoid errors such as "make: go: No such file or directory" in subsequent steps.

### Build
To build and push images from the source, use the `update_images.sh` script. This script performs the following:
1. Build specified images from the source.
2. Push built images to the specified registry.

#### Usage
Run `./update_images.sh --help` to get detailed information.

```
Usage: ./update_images.sh [OPTIONS] [COMPONENTS...]
Options:
        --build: Build specified components.
        --push: Push specified components to the registry.
        --setup-registry: Setup local registry at port 5000.
        --registry: Specify the registry (default is localhost:5000).
        --tag: Specify the tag (default is latest).
Components available (default is all):
         gmcManager dataprep-usvc embedding-usvc reranking-usvc torchserve retriever-usvc ingestion-usvc llm-usvc in-guard-usvc out-guard-usvc ui-usvc otelcol-contrib-journalctl
Example: ./update_images.sh --build --push --registry my-registry embedding-usvc reranking-usvc
```

### Install chat Q&A
To streamline the deployment process, use the `install_chatqna.sh` script.

#### Configure

Set your huggingface token changing value inside `helm/values.yaml` tokens.hugToken or use script:

```
./set_values.sh -g $YOUR_HUGGING_TOKEN
```
> [!NOTE]
> Grafana POD will require internet access to download a plugin. To enable this, you might need to configure the proxy settings. Please adjust the proxy settings in the [Grafana Helm values](../telemetry/helm/values.yaml)

#### Usage

Execute defined pipeline defined in [microservices-connector/config/samples](./microservices-connector/config/samples/)

Run `./install_chatqna.sh --help` to get detailed information.
```
Usage: ./install_chatqna.sh [OPTIONS]
Options:
        --aws: Use aws registry.
        --grafana_password (REQUIRED with --telemetry): Initial password for grafana.
        --kind: Changes dns value for telemetry(kind is kube-dns based).
        --deploy <PIPELINE_NAME>: Start the deployment process.
        Pipelines available: gaudi_torch_guard,gaudi_torch,gaudi,switch_gaudi,switch_xeon,xeon_llm_guard,xeon_torch_llm_guard,xeon_torch,xeon
        --tag <TAG>: Use specific tag for deployment.
        --test: Run a connection test.
        --telemetry: Start telemetry services.
        --registry <REGISTRY>: Use specific registry for deployment.
        --ui: Start auth and ui services (requires deployment).
        --upgrade: Helm will install or upgrade charts.
        -cd|--clear-deployment: Clear deployment services.
        -ct|--clear-telemetry: Clear telemetry services.
        -cu|--clear-ui: Clear auth and ui services.
        -ca|--clear-all: Clear the all services.
        -h|--help: Display this help message.
Example: ./install_chatqna.sh --deploy gaudi_torch --telemetry --ui --grafana_password=changeitplease
```
Example command:
```
./install_chatqna.sh --deploy chatQnA_gaudi_torch_guard --auth --telemetry --ui
```

In the above case, the run should end with having all pods defined in [chatQnA_gaudi_torch_guard.yaml](./microservices-connector/config/samples/chatQnA_gaudi_torch.yaml) being in a running state.

### Test:
To verify the functionality of the Chat Q&A pipeline, run the `test_connecton.sh` script. It will execute a test query and display the response.

### Access UI from your local machine

To access UI please forward the below ports when connecting to the server:

```
    LocalForward 1234 localhost:1234
    LocalForward 4173 localhost:4173
    LocalForward 3000 localhost:3000
``` 

Next, you can access Enterprise RAG UI by typing in the web browser: `http://localhost:4173/` on your local machine.

