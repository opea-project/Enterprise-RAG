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
- installed golang-go (version 1.21)
- installed helm. You can follow the instructions [here](https://helm.sh/docs/intro/install/)

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

### Introduction

There are `2` components in this repo:

- 1. `manager`: controller manager to handle GMC CRD
- 2. `router`: route the traffic among the microservices defined in GMC

#### How to build these binaries?

```sh
make build
```

#### How to build docker images for these 2 components?

```sh
make docker.build
```

#### How to delete these components' binaries?

```sh
make clean
```

### push images to local registry

create local registry:

```sh
docker run -d -p 5000:5000 --name local-registry registry:2
```

next build images and push to local registry:

```sh
bash update_images.sh
```

### prepare manifests

Before running the excution we need to update values in manifests 
```sh
bash set_envs.sh <your HF token>
```
### executing helm chart

This helm chart will install the following components of GMC:

- GMC CRD
- GenAI Components and GMC Router manifests
- GMC Manager

**NOTE: Because helm doesn't support updating/deleting CRD, you need to manually delete the CRD before upgrading the GMC helm chart.**

**NOTE:**
before apply the manifests, please replace your own huggingface tokens in the manifests

**NOTE:**
GMC manager, GenAI components and GMC router manifests are deployed in any namespace. Here we use `system` as an examep:

```console
helm install -n system --create-namespace gmc helm
```

## Check the installation result

Run the command `kubectl get pod -n system` to make sure all pods are running:

```
NAME                            READY   STATUS    RESTARTS   AGE
gmc-contoller-8bcb9d469-l6fsj   1/1     Running   0          55s
```

## Next step

After the GMC is installed, you can follow the [GMC user guide](../usage_guide.md) for sample use cases.

## Uninstall

**Delete the instances (CRs) from the cluster if you have ever deployed the instances from GMC user guide:**

```sh
kubectl delete -k config/samples/
```

**UnDeploy the GMC manager and GenAI components and GMC router manifest from the cluster:**

```sh
helm delete -n system gmc
```

**Delete the APIs(CRDs) from the cluster:**

```sh
kubectl delete crd gmconnectors.gmc.opea.io
```

