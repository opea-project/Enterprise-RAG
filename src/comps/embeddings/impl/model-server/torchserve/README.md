# TorchServe Embedding Model Server

This folder contains the implementation of the Torchserve server for an embedding model.

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
```
curl http://localhost:8090/ping
```

Expected output:
```
{
  "status": "Healthy"
}
```

Next, you can query the management endpoint to list the models currently loaded in the TorchServe instance:

```
curl http://localhost:8091/models
```

Expected output:
```
{
  "models": [
    {
      "modelName": "bge-large-en-v1.5",
      "modelUrl": "bge-large-en-v1.5.tar.gz"
    }
  ]
}
```

This output provides information about the models that have been registered with the server. This confirmation ensures that your specific model is available for inference.

To make a prediction using the loaded model, you can send a request to the prediction endpoint with your input text. A response will be in the form of a JSON array representing the embedding vector for the provided input text. Use the following curl command to request a prediction from the loaded model in this example. Note that bge-large-en-v1.5 is a model's identifier.

```bash
curl http://localhost:8090/predictions/bge-large-en-v1.5 \
    -H "Content-Type: text/plain" \
    --data "What is machine learning?"
```
Expected output:

```
[
  0.02112000435590744,
  0.02303740382194519,
  -0.04439482465386391,
  ...
]
```

### 🚀 2. Deploy TorchServe Service with Embedding Microservice using Docker Compose (Option 2)

To launch TorchServe Service along with the Embedding Microservice, follow these steps:


#### 2.1. Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case. Refer to [Torchserve configuration](https://pytorch.org/serve/configuration.html) for supported variables.

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker

docker compose --env-file=.env up --build -d
```

#### 2.3. Verify the Services

- Test the `embedding-torchserve-model-server` using the following command:
    ```bash
    # check status
    curl http://localhost:8090/ping

    # list loaded models
    curl http://localhost:8091/models

    # inference; replace bge-large-en-v1.5 with the desired model identifier from the loaded models
    curl http://localhost:8090/predictions/bge-large-en-v1.5 \
        -H "Content-Type: text/plain" \
        --data "What is machine learning?"
    ```

- Check the `embedding-tei-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-tei-microservice` using the following command:
    ```bash
    curl localhost:6000/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
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
