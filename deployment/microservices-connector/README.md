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

**CRD** defines are at config/crd/bases/
**API** is api/v1alpha3/
**Controller** is at internal/controller

### Prerequisites

- Access to a Kubernetes v1.11.3+ cluster
- install make
- installed docker (need to build docker images)
- installed golang-go (version 1.22.1)
- installed helm. You can follow the instructions [here](https://helm.sh/docs/intro/install/)
- installed and configured awscli

#### setup docker

sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
apt-cache policy docker-ce
sudo apt install docker-ce

mkdir -p /etc/systemd/system/docker.service.d
sudo vi /etc/systemd/system/docker.service.d/proxy.conf

```
[Service]
Environment="HTTP_PROXY=<http_proxy>"
Environment="HTTPS_PROXY=<https_proxy>"
Environment="NO_PROXY="<no_proxy>"
```

sudo vim ~/.docker/config.json

```
{
  "proxies": {
    "default": {
       "httpProxy": "<http_proxy>",
       "httpsProxy": "<https_proxy>"
        }
    } 
}
```
#### install_golang.go
 
execute `bash install_go.sh` next `source ~/.profile`

#### install adn configure aws cli
execute `apt-get install awscli`
next execute `aws configure` ,type your AWS credentials set region to us-west-2

### Quick Start using default images.

To simplify deployment process the `run_RAG.sh` script has been created.

Put in  [values.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/helm/values.yaml) your proxy settings for example:
```
proxy:
  httpProxy: "http://proxy-dmz.intel.com:911"
  httpsProxy: "http://proxy-dmz.intel.com:912"
  noProxy: ".intel.com,intel.com,localhost,127.0.0.1,.svc,.svc.cluster.local"

tokens:
  hugToken: "<your HF token>"
```
Make sure you have default folder created for opea models `mkdir /mnt/opea-models` 

Next execute defined pipeline defined in [config/samples](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/config/samples/) 

Example command:
`./run_RAG.sh dataprep_xeon_torch`

In the above case the run should end with having all pods defined in [chatQnA_dataprep_xeon_torch.yaml](https://github.com/intel-innersource/applications.ai.enterprise-rag.enterprise-ai-solution/blob/main/deployment/microservices-connector/config/samples/chatQnA_dataprep_xeon_torch.yaml) in running state.

### Test the solution:
You can run `./test_connecton.sh` script to test the check if chatqna pipeline is functional. The reply should provide you the output for test question defined the script.

### Build your own images and push them to your registry. 

There is a script `update_images.sh` that allows to:
1. build defined images from source
2. push images to user defined registry
Run `./update_images.sh --help` to get detail information.

```
root@node1:/home/sdp/applications.ai.enterprise-rag.enterprise-ai-solution/deployment/microservices-connector# ./update_images.sh --help
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
