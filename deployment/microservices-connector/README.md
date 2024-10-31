# genai-microservices-connector(GMC)

This repo defines the GenAI Microservice Connector(GMC) for OPEA projects. GMC can be used to compose and adjust GenAI pipelines dynamically
on Kubernetes. It can leverage the microservices provided by [GenAIComps](https://github.com/opea-project/GenAIComps) and external services to compose GenAI pipelines. External services might be running in a public cloud or on-prem by providing a URL and access details such as an API key and ensuring there is network connectivity. It also allows users to adjust the pipeline on the fly like switching to a different Large Language Model(LLM), adding new functions into the chain(like adding guardrails), etc. GMC supports different types of steps in the pipeline, like sequential, parallel, and conditional.

Please refer to this [usage_guide](./usage_guide.md) for sample use cases.

## Description

The GenAI Microservice Connector(GMC) contains the CustomResourceDefinition(CRD) and its controller to bring up the services needed for a GenAI application.
Istio Service Mesh can also be leveraged to facilitate communication between microservices in the GenAI application.


## Getting Started

- **CRD** defines are at [config/crd/bases/](config/crd/bases/)
- **API** is [api/v1alpha3/](api/v1alpha3/)
- **Controller** is at [internal/controller/](internal/controller/)
