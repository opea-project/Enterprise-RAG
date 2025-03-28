# TorchServe Reranks Model Server

This folder contains the implementation of the Torchserve server for a reranking model.

[TorchServe](https://pytorch.org/serve/) is a lightweight, scalable, and easy-to-use model serving library for PyTorch models. It provides a RESTful API for serving trained models, allowing users to deploy and serve their models in production environments. Moreover, Torchserve supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 1. Start the TorchServe Service via script (Option 1)

#### 1.1. Run the script

```bash

chmod +x run_torchserve.sh
./run_torchserve.sh
```

The script initiates a Docker container with the TorchServe model server running on port `TORCHSERVE_PORT` (default: **8090**) to handle inference requests. Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

#### 1.2. Verify the TorchServe Service

Send a ping request to the inference endpoint to verify that the server is operational:
```bash
curl http://localhost:8090/ping
```

Expected output:
```json
{
  "status": "Healthy"
}
```

Next, you can query the management endpoint to list the models currently loaded in the TorchServe instance:

```bash
curl http://localhost:8091/models
```

Expected output:
```json
{
  "models": [
    {
      "modelName": "bge-reranker-base",
      "modelUrl": "bge-reranker-base.tar.gz"
    }
  ]
}
```

This output provides information about the models that have been registered with the server. This confirmation ensures that your specific model is available for inference.

To make a prediction using the loaded model, you can send a request to the prediction endpoint with your input text. A response will be in the form of a JSON array representing the embedding vector for the provided input text. Use the following curl command to request a prediction from the loaded model in this example. Note that bge-reranker-base is a model's identifier.

```bash
curl http://localhost:8090/predictions/bge-reranker-base \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```
Expected output:

```
[
  -1.9903568029403687,
  2.7947142124176025
]
```

### 🚀 2. Deploy TorchServe Service with Reranks Microservice using Docker Compose (Option 2)

To launch TorchServe Service along with the Reranks Microservice, follow these steps:


#### 2.1. Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case. Refer to [Torchserve configuration](https://pytorch.org/serve/configuration.html) for supported variables.

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker

docker compose --env-file=.env up --build -d
```

#### 2.3. Verify the Services

- Test the `reranks-torchserve-model-server` using the following command:
    ```bash
    # check status
    curl http://localhost:8090/ping

    # list loaded models
    curl http://localhost:8091/models

    # inference; replace bge-reranker-base with the desired model identifier from the loaded models
    curl http://localhost:8090/predictions/bge-reranker-base \
        -X POST \
        -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
        -H 'Content-Type: application/json'
    ```

- Check the `reranks-torchserve-microservice` status:
    ```bash
    curl http://localhost:8000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `reranks-torchserve-microservice` using the following command:
    ```bash
    curl  http://localhost:8000/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is DL?", "retrieved_docs": [{"text":"DL is not..."}, {"text":"DL is..."}]}' \
        -H 'Content-Type: application/json'
    ```


#### 2.4. Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

docker compose down
```


## Additional Information
### Folder Structure

- `docker/`: Contains a Dockerfile and support files.
- `model/`: Contains a model handler for Torchserve and its support files.
