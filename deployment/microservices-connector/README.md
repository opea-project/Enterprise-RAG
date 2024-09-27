# genai-microservices-connector(GMC)

This repo defines the GenAI Microservice Connector(GMC) for OPEA projects. GMC can be used to compose and adjust GenAI pipelines dynamically
on kubernetes. It can leverage the microservices provided by [GenAIComps](https://github.com/opea-project/GenAIComps) and external services to compose GenAI pipelines. External services might be running in a public cloud or on-prem by providing an URL and access details such as an API key and ensuring there is network connectivity. It also allows users to adjust the pipeline on the fly like switching to a different Large language Model(LLM), adding new functions into the chain(like adding guardrails),etc. GMC supports different types of steps in the pipeline, like sequential, parallel and conditional.

Please refer this [usage_guide](./usage_guide.md) for sample use cases.

## Description

The GenAI Microservice Connector(GMC) contains the CustomResourceDefinition(CRD) and its controller to bring up the services needed for a GenAI application.
Istio Service Mesh can also be leveraged to facilicate communication between microservices in the GenAI application.

## Architecture

![GMC Architecture](./architecture.png)

## Personas

![GMC Personas](./personas.png)

## Getting Started

- **CRD** defines are at config/crd/bases/
- **API** is api/v1alpha3/
- **Controller** is at internal/controller

### Prerequisites

- Access to a Kubernetes v1.11.3+ cluster
- Debian-based Linux OS
- Prepared Gaudi node (running on CPU is possible but will reduce performance significantly). [prepare Gaudi node on K8s setup](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/simplify-env-setup/deployment/microservices-connector/PREPARE_GAUDI.md)
- AWS account to login into ECR ( this will be optional for future releases)

------------

### Quickstart with oneclick script

You can proceed through configuration, deployment and test connection using `one_click_chatqna.sh`:

#### Usage
```
./one_click_chatqna.sh -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY -r REGION [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -g HUG_TOKEN
```
Proxy variables are optional.

###  Configure
The `configure.sh` script automates the setup process by installing necessary tools needed:

- `make`
- `docker`
- `golang` (version 1.22.1)
- `helm`
- `awscli`

#### Usage:
```
./configure.sh -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY -r REGION [-p HTTP_PROXY] [-u HTTPS_PROXY] [-n NO_PROXY] -g HUG_TOKEN
```
Proxy variables are optional.
> [!NOTE]
> The images are stored on AWS to simplify deployment process. The images can be build directly from the source using `update_images.sh` script and pushed to user defined registry. In such case please modify paths to images in [values.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/helm/values.yaml)

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
> Grafana POD will require access to internet do download plugin. In order to do that we need to setup proxy settings here:[grafana_proxy](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/simplify-env-setup/telemetry/helm/values.yaml)

Create the default folder for OPEA models:
```
mkdir /mnt/opea-models
```

Execute defined pipeline defined in [config/samples](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/config/samples/)

You can check available options by executing install_chatqna.sh --help
```
Usage: install_chatqna.sh [OPTIONS]
Options:
        --deploy <PIPELINE_NAME>: Start the deployment process (default).
        Pipelines available:
                gaudi_torch_guard
                gaudi_torch
                gaudi
                switch_gaudi
                switch_xeon
                xeon_llm_guard
                xeon_torch_llm_guard
                xeon_torch
                xeon
        --test: Run a connection test.
        --auth: Start authentication service with Keycloak.
        --ui: Startui service (requires Keycloak and deployment services).
        --telemetry: Start telemetry services.
        --clear: Clear the cluster and stop auth and telemetry services.
        --dataprep: Start dataprep pipeline.
        --help: Display this help message.
Example: install_chatqna.sh --deploy gaudi
Example: install_chatqna.sh --deploy gaudi_torch --telemetry --dataprep --auth --ui
```
Example command:
```
./install_chatqna.sh --deploy xeon_torch --dataprep --auth --telemetry --ui
```

In the above case the run should end with having all pods defined in [chatQnA_dataprep_xeon_torch.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/config/samples/chatQnA_dataprep_xeon_torch.yaml) in running state.

### Test:
To verify the functionality of the Chat Q&A pipeline, run the `test_connecton.sh` script. It will execute a test query and display the response.

### Access UI from Your Local Machine

To access the UI on your machine, you need to forward specific ports when connecting to the server.
Below are some common methods to achieve this, but feel free to use any other method that suits your needs.

#### Common Methods for Port Forwarding

1. **Adding to `.ssh/config` File:**

You can add the following lines to your `~/.ssh/config` file to set up port forwarding:

```
Host <your_server_alias>
    HostName <IP of server host>
    LocalForward 1234 localhost:1234
    LocalForward 4173 localhost:4173
    LocalForward 3000 localhost:3000
```
Connect to the server using the alias you defined:

`
ssh <your_server_alias>
`

2. **Passing with `ssh` Command:**

    Alternatively, you can pass the port forwarding options directly with the `ssh` command:

    ```sh
    ssh -L 1234:localhost:1234 -L 4173:localhost:4173 -L 3000:localhost:3000 your_username@your_server_address
    ```

#### Accessing the UI

Once you have set up port forwarding, you can access the Enterprise RAG UI by typing the following URL in your web browser on your local machine:

```plaintext
http://localhost:4173/
```

This will allow you to interact with the UI as if it were running locally on your machine.
 

