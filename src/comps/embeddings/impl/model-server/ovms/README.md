# OVMS Model Server

This folder contains the scripts to run an embedding model with OpenVINO™ Model Server (OVMS).

[OVMS](https://github.com/openvinotoolkit/model_server) is an open-source model server that provides a scalable and efficient solution for deploying deep learning models in production environments. It is built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

For detailed information and practical examples of how to use OpenVINO Model Server (OVMS), please refer to the OVMS documentation on the official [OpenVINO Toolkit GitHub page](https://github.com/openvinotoolkit/model_server/blob/main/docs/home.md).


## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```


### 🚀 1. Start the TEI Service via script (Option 1)
#### 1.1. Run the script
```bash
chmod +x run_ovms.sh
./run_ovms.sh
```

The script initiates a Docker container with the OVMS server running on port (`OVMS_PORT`, default: **9000**) for serving model embedding. Configuration settings are specified in the [docker/.env](docker/.env) file. You can adjust these settings either by modifying the dotenv file or by exporting environment variables.

#### 1.2. Verify the OVMS

If you'd like to check whether the endpoint is already running, check out following request:
```bash
export MODEL_NAME="bge-large-en-v1.5"
curl http://localhost:9000/v2/models/${MODEL_NAME}
```

If the endpoint is correctly running, it should print out an output similar to the one below:
```json
{
   "name":"bge-large-en-v1.5",
   "versions":["1"],
   "platform":"OpenVINO",
   "inputs":[
      {
         "name":"Parameter_1",
         "datatype":"BYTES",
         "shape":[-1]
      }
   ],
   "outputs":[
      {
         "name":"last_hidden_state",
         "datatype":"FP32",
         "shape":[-1,-1,1024]
      }
   ]
}
```

### 🚀 2. Deploy OVMS with Embedding Microservice using Docker Compose (Option 2)

To launch OVMS along with the Embedding Microservice, follow these steps:

#### 2.1. Modify the environment configuration file to align it to your case

Modify the [./docker/.env](./docker/.env) file to suit your use case.

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose:

```bash
cd docker

docker compose up --build -d
```
#### 2.3. Verify the Services

- Test the `embedding-torchserve-model-server` using the following command:
   ```bash
   export MODEL_NAME="bge-large-en-v1.5"
   curl -X POST http://localhost:9000/v2/models/${MODEL_NAME}/infer -H 'Content-Type: application/json' -d '{"inputs" : [ {"name" : "Parameter_1", "shape" : [1], "datatype"  : "BYTES", "data" : ["What is Intel Gaudi?"]}]}'
   ```
- Check the `embedding-ovms-microservice` status:
    ```bash
    curl http://localhost:6000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `embedding-ovms-microservice` using the following command:
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
- `combine_models.py`: Combines an embedding model and a tokenizer model using OpenVINO™, then saves the combined model for use with OVMS.
