# Embeddings Microservice

The Embedding Microservice is designed to efficiently convert textual strings into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the semantic essence of the input text, making it ideal for applications in natural language processing, information retrieval, and similar fields.

**Key Features**

- **High Performance**: Optimized for quick and reliable conversion of textual data into vector embeddings.
- **Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.
- **Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.
- **Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are able to configure and build embedding-related services according to their actual needs.

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server                | langchain | llama_index |
| ------------                | ----------| ------------|
| [torchserve](./torchserve)  | &#x2713;  | &#x2717;    |
| [TEI](./tei)                | &#x2713;  | &#x2713;    |
| [OVMS](./ovms)              | &#x2713;  | &#x2717;    |
| [mosec](./mosec)            | &#x2713;  | &#x2717;    |

## Configuration Options

The configuration for the OPEA Embedding Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `EMBEDDING_USVC_PORT`                 | The port of the microservice, by default 6000.                                                                        |
| `EMBEDDING_MODEL_NAME`                | The name of language model to be used (e.g., "bge-large-en-v1.5")                                             |
| `EMBEDDING_CONNECTOR`                 | The framework used to connect to the model. Supported values: 'langchain', 'llama_index' |
| `EMBEDDING_MODEL_SERVER`              | Specifies the type of model server (e.g. "tei", "ovms")                                                               |
| `EMBEDDING_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint, e.g., "http://localhost:8090"                                                       |


## Getting started

### Prerequisite: Start Embdedding Model Server

The OPEA Embedding Microservice interacts with an Embedding model endpoint, which must be operational and accessible at the the URL specified by the `EMBEDDING_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. 


Currently, we provide these ways to implement a model server for an embedding:

1. Build embedding model server based on the [**_TEI endpoint_**](./impl/model-server/tei/), which provides more flexibility, but may bring some network latency.
2. Utilize [**_Torchserve_**](./impl/model-server/torchserve/), which supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.
3. Utilize [**_Mosec_**](./impl/model-server/mosec/) to run a model server with Intel® Extension for PyTorch* optimizations.
4. Run an embedding model server with [**_OVMS_**](./impl/model-server/ovms/) - an open source model server built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

Refer to `README.md` of a particular library to get more information on starting a model server.


## 🚀1. Start OPEA Embedding Microservice with Python (Option 1)

To start the Embedding microservice, you need to install requirements first.

#### 1.1. Install Requirements
First, install essential requirements for the microservice:

```bash
# common
pip install -r impl/microservice/requirements.txt
```

Next, install specific model server requirements, depending on choosen model server:

```bash
# for langchain
pip install -r impl/microservice/requirements/langchain.txt

# for llama_index
pip install -r impl/microservice/requirements/llama_index.txt
```

#### 1.2. Start Microservice

```bash
python opea_embedding_microservice.py
```

### 🚀2. Start OPEA Embedding Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../

# for langchain
docker build --target langchain -t opea/embedding:langchain -f comps/embeddings/impl/microservice/Dockerfile .

# for llama_index
docker build --target llama_index -t opea/embedding:llama_index -f comps/embeddings/impl/microservice/Dockerfile .

```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:

Ensure that the `EMBEDDING_CONNECTOR` corresponds to the specific image built with the relevant requirements. Below are examples for both Langchain and Llama Index:

```bash
# for langchain
docker run -d --name="embedding-microservice" \
  -e EMBEDDING_CONNECTOR=langchain \
  --net=host \
  --ipc=host \
  opea/embedding:langchain
```

```bash
# for llama_index
docker run -d --name="embedding-microservice" \
  -e EMBEDDING_CONNECTOR=llama_index \
  --net=host \
  --ipc=host \
  opea/embedding:llama_index
```

If the model server is running at a different endpoint than the default, update the `EMBEDDING_MODEL_SERVER_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
# for langchain
docker run -d --name="embedding-microservice" \
  -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://localhost:8090" \
  -e EMBEDDING_MODEL_NAME="bge-large-en-v1.5" \
  -e EMBEDDING_CONNECTOR="langchain" \
  -e EMBEDDING_MODEL_SERVER="tei" \
  --net=host \
  --ipc=host \
  opea/embedding:langchain
```

```bash
# for llama_index
docker run -d --name="embedding-microservice" \
  -e EMBEDDING_MODEL_SERVER_ENDPOINT="http://localhost:8090" \
  -e EMBEDDING_MODEL_NAME="bge-large-en-v1.5" \
  -e EMBEDDING_CONNECTOR="llama_index" \
  -e EMBEDDING_MODEL_SERVER="tei" \
  --net=host \
  --ipc=host \
  opea/embedding:llama_index
```


### 3. Verify the OPEA Embedding Microservice

#### 3.1. Check Status

```bash
curl http://localhost:6000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The embedding microservice accepts input as either a single text string or multiple documents containing text. Below are examples of how to structure the reques

**Example Input**

 For a single text input:
  ```bash
  curl http://localhost:6000/v1/embeddings \
    -X POST \
    -d '{"text":"Hello, world!"}' \
    -H 'Content-Type: application/json'
  ```

For multiple documents:
```bash
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"docs": [{"text":"Hello, world!"}, {"text":"Hello, world!"}]}' \
  -H 'Content-Type: application/json'
```

**Example Output**

The output of an embedding microservice is a JSON object that includes the input text, the computed embeddings, and additional parameters.

For a single text input:
```json
{
  "id":"d4e67d3c7353b13c3821d241985705b1",
  "text":"Hello, world!",
  "embedding":[ 0.024471128, 0.047724035, -0.02704641, 0.0013827643 ],
  "search_type":"similarity",
  "k":4,
  "distance_threshold":null,
  "fetch_k":20,
  "lambda_mult":0.5,
  "score_threshold":0.2z,
  "metadata": {}
}
```

For multiple documents:
```json
{
  "id":"d4e67d3c7353b13c3821d241985705b1",
  "docs": [
    {
      "id": "27ff622c495813be476c892bb6940bc5",
      "text":"Hello, world!",
      "embedding":[ 0.024471128, 0.047724035, -0.02704641, 0.0013827643 ],
      "search_type":"similarity",
      "k":4,
      "distance_threshold":null,
      "fetch_k":20,
      "lambda_mult":0.5,
      "score_threshold":0.2
    },
    {
      "id": "937f9b71a2fa0e6437e33c55bec8e1ea",
      "text": "Hello, world!",
      "embedding":[ 0.024471128, 0.047724035, -0.02704641, 0.0013827643 ],
      "search_type":"similarity",
      "k":4,
      "distance_threshold":null,
      "fetch_k":20,
      "lambda_mult":0.5,
      "score_threshold":0.2,
      "metadata": {}
    }
  ]
}
```


## Additional Information
### Project Structure

The project is organized into several directories:
- `impl/`: This directory contains the implementation. It includes the microservice folder with the Dockerfile for the microservice, and the `model_server` directory, which provides setup and running instructions for various model servers, such as TEI or OVMS.
- `utils/`: This directory contains utility scripts and modules that are used by the OPEA Embedding Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── .env
  │   │   ├── Dockerfile
  │   │   └── requirements.txt
  │   │   └── requirements/
  │   │      ├── langchain.txt
  │   │      └── lama_index.txt
  │   │
  │   ├── model_server/
  │   │   ├── tei/
  │   │   │   ├── README.md
  │   │   │   ├── run_tei.sh
  │   │   │   └── docker/
  │   │   │       ├── .env
  │   │   │       └── docker-compose.yml
  │   │   │  
  │   │   └── ...
  │   └── ...
  │
  ├── utils/
  │   ├── opea_embedding.py
  │   ├── api_config/
  │   │   └── api_config.yml
  │   │
  │   └── wrappers/
  │       ├── wrapper.py
  │       ├── wrapper_langchain.py
  │       └── wrapper_lamaindex.py
  │   
  ├── README.md
  └── opea_embedding_microservice.py
```

#### Tests
- `src/tests/unit/embeddings/`: Contains unit tests for the OPEA Embedding Microservice components

