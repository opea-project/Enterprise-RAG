TODO: modify README for embedding microservice's docker information

# Embeddings Microservice

The Embedding Microservice is designed to efficiently convert textual strings into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the semantic essence of the input text, making it ideal for applications in natural language processing, information retrieval, and similar fields.

**Key Features**

- **High Performance**: Optimized for quick and reliable conversion of textual data into vector embeddings.
- **Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.
- **Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.
- **Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are able to configure and build embedding-related services according to their actual needs.

## Example input

Embedding microservice as an input accepts a string of text. Example request can looks as follows:

```bash
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'
```

## Example output

Output of an embedding microservice is a json that stores an input text, computed embeddings and other parameters.
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
  "score_threshold":0.2
}
```

## 🚀1. Start Microservice

For all of the implementations of the microservice, you need to install requirements first.

#### Install requirements

To install the requirements, run the following commands:

```bash
# First, install essential requirements for the microservice
pip install -r impl/microservice/requirements.txt

# Next, install specific model server requirements, depending on choosen model server:

# For langchain model server, use the following command:
pip install -r impl/microservice/requirements/langchain.txt

# for llama_index model server, use the following command:
pip install -r impl/microservice/requirements/llama_index.txt
```

### 1.1 Start Embedding Model Server
Currently, we provide 3 ways to implement a model server for an embedding:

1. Build embedding model server based on the [**_TEI endpoint_**](./impl/model-server/tei/), which provides more flexibility, but may bring some network latency.
2. Utilize [**_Torchserve_**](./impl/model-server/torchserve/), which supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.
3. Utilize [**_Mosec_**](./impl/model-server/mosec/) to run a model server with Intel® Extension for PyTorch* optimizations.
4. Run an embedding model server with [**_OVMS_**](./impl/model-server/ovms/) - an open source model server built on top of the OpenVINO™ toolkit, which enables optimized inference across a wide range of hardware platforms.

Refer to `README.md` of a particular library to get more information on starting a model server.

### 1.2 Start Embedding Microservice with Python (Option 1)

Once you start a chosen model server, it is time to initialize the embedding microservice. You can do so by running following commands:

```bash
EMBEDDING_MODEL_NAME="bge-large-en-v1.5"
EMBEDDING_MODEL_SERVER="tei"
FRAMEWORK="langchain"
EMBEDDING_MODEL_SERVER_ENDPOINT="http://localhost:8090"
python opea_embedding_microservice.py
```

### 1.3 Start Embedding Microservice with Docker (Optional 2)

#### Build Docker Image

To build the Docker image, follow these steps:

#### Build Langchain Docker (Option a)
```bash
cd ../../
docker build -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```

#### Build LlamaIndex Docker (Option b)
```bash
cd ../../
docker build -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/llama_index/docker/Dockerfile .
```

#### Run the Docker container

#### With CLI

To run the Docker container with CLI, use the following command:

```bash
docker run -d --name="embedding-tei-server" -p 6000:6000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e TEI_EMBEDDING_MODEL_NAME=$TEI_EMBEDDING_MODEL_NAME opea/embedding-tei:latest
```

## 3. Test Embedding Microservice

### 3.1 Check Service Status

To check the status of the microservice, run the following command:
```bash
curl http://localhost:6000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Example Embedding Microservice request

```bash
curl http://localhost:6000/v1/embeddings \
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'
```
