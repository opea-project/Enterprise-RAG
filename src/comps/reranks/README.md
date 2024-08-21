# OPEA Reranking Microservice

The Reranking Microservice, fueled by reranking models, stands as a straightforward yet immensely potent tool for semantic search. When provided with a query and a collection of documents, reranking swiftly indexes the documents based on their semantic relevance to the query, arranging them from most to least pertinent. This microservice significantly enhances overall accuracy. In a text retrieval system, either a dense embedding model or a sparse lexical search index is often employed to retrieve relevant text documents based on the input. However, a reranking model can further refine this process by rearranging potential candidates into a final, optimized order.


## Example input

Reranking microservice as an input accepts a json. An example request can look as follows:

```bash
  curl http://localhost:8000/v1/reranking \
    -X POST \
    -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}], "top_n":1}' \
    -H 'Content-Type: application/json'
```


## Example output

The output of the reranking microservice is a json that contains the final prompt query, constructed based on the top_n retrieved documents.
```json

{
  "id":"c345dc52ce3f806e987f07eab8750340",
  "model":null,
  "query":"### You are a helpful, respectful, and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results:  Deep learning is... \n\n### Question: What is Deep Learning? \n\n### Answer:",
  "max_new_tokens":1024,
  "top_k":10,
  "top_p":0.95,
  "typical_p":0.95,
  "temperature":0.01,
  "repetition_penalty":1.03,
  "streaming":true
  }
```

## Configuration Options

Configuration for the OPEA Reranking Microservice is defined in the [config.ini](./config.ini) file, and can be adjusted there or via correspoding environment variables.

Examplary configuration:

```ini
[Logging]
log_level=INFO
log_path=/tmp/opea/microservices/reranking/reranking.log

[OPEA_Microservice]
name=opea_service@reranking
host=0.0.0.0
port=8000

[Service]
url=http://localhost:6060/rerank
```

What each section and option does:

| **Configuration Option**  | **Default in `config.ini`** | **Environment Variable** | **Description**                                                              |
|---------------------------|-----------------------------|--------------------------|------------------------------------------------------------------------------|
| **[Logging]**             |                             |                          | This section contains options related to logging.                            |
| `log_level`               | Defined in `config.ini`     | `RERANKING_LOG_LEVEL`    | The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).                   |
| `log_path`                | Defined in `config.ini`     | `RERANKING_LOG_PATH`     | The path to the log file.                                                    |
| **[OPEA_Microservice]**   |                             |                          | This section contains options related to the microservice itself             |
| `name`                    | Defined in `config.ini`     | `RERANKING_NAME`         | The name of the microservice.                                                |
| `host`                    | Defined in `config.ini`     | `RERANKING_HOST`         | The host of the microservice.                                                |
| `port`                    | Defined in `config.ini`     | `RERANKING_PORT`         | The port of the microservice.                                                |
| **[Service]**             |                             |                          | This section contains options related to the reranking service (e.g TEI).    |
| `url`                     | Defined in `config.ini`     | `RERANKING_SERVICE_URL`  | The URL of the reranking service.                                            |


## Getting started

For all of the implementations of the microservice, you need to install requirements first.

### 1. Install requirements

To install the requirements, run the following commands:

```bash
pip install -r impl/microservice/requirements.txt
```

### 2. Start Reranking Model Server 

The OPEA Reranking Microservice interacts with a rerank model endpoint that must be operational and reachable at the URL specified by the `RERANKING_SERVICE_URL` environment variable or the `url` option in the `Service` section of the [config.ini](config.ini) file.

Depending on the model server you want to use for obtaining scores, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. For more details on the supported ranking model servers, refer to section [Support Matrix for Model Server](4-support-matrix-for-model-server).


#### Support Matrix for Model-Server

Support for specific ranking model servers with Dockerfiles or build instruction.

| Model server name               |  Status   | 
| ---------------------------     | --------- | 
| [TEI](./impl/model_server/tei/) | &#x2713;  | 
| OVMS                            | &#x2717;  |


### 🚀3. Start OPEA Reranking Microservice with Python (Option 1)

  ```bash
  $ python opea_reranking_microservice.py


  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
  [2024-08-11 15:45:51,113] [    INFO] - HTTP server setup successful
  ```

### 🚀4. Start OPEA Reranking Microservice with Docker (Option 2)

#### 4.1. Build the Docker Image:
Use the docker build command to create the Docker image. First, navigate to the src directory in the project’s root folder, as this directory contains the necessary source code required for building the image.
```bash
cd ../../
docker build -t opea/reranking:latest \
  -f comps/reranks/impl/microservice/Dockerfile .
```
#### 4.2. Run the Docker Container:
Once the image is built, you can run it using the docker run command. Before running the image, ensure the Model Server is already running. Please, refer to the documentation in the [model_server directory](./model_server) for instructions on how to run the specific model.

For example, assuming the TEI Model is serving rankings at `http://localhost:6060/rerank`, you can run the OPEA Reranking Microservice with the following command:

```bash
docker run -d --name="reranking-tei-microservice" \
  -e RERANKING_SERVICE_URL=http://localhost:6060/rerank \
  --net=host \
  --ipc=host \
  opea/reranking:latest
```

## 5. OPEA Reranking Microservice API

### 5.1. Check Status

  ```bash
  curl http://localhost:8000/v1/health_check \
    -X GET \
    -H 'Content-Type: application/json'
  ```

### 5.2. Usage

  ```bash
  curl http://localhost:8000/v1/reranking \
    -X POST \
    -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
    -H 'Content-Type: application/json'
  ```


  You can add the parameter `top_n` to specify the return number of the reranker model, default value is 1.

  ```bash
  curl http://localhost:8000/v1/reranking \
    -X POST \
    -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}], "top_n":2}' \
    -H 'Content-Type: application/json'
  ```


### Additional Information
   
#### Project Structure

  The project is organized into several directories:

  - `impl/`: This directory contains the implementation of the supported reranking service. It includes the `model_server` directory, which contains instructions for setting up and running different model servers, for example TEI.

- `utils/`: This directory contains utility scripts and modules that are used by the OPEA Reranking Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── Dockerfile
  │   │   └── requirements.txt
  │   │
  │   ├── model_server/
  │   │   ├── tei/
  │   │   │   ├── README.md
  │   │   │   └── docker/
  │   │   │       ├── docker-compose.yml
  │   │   │       └── .env
  │   │   │  
  │   │   └── ...
  │   └── ...
  │
  ├── utils/
  │   ├── opea_reranking.py
  │   └── prompt.py
  │
  ├── README.md
  ├── config.ini
  └── opea_reranking_microservice.py
```

#### Tests
- `src/tests/unit/rerankers/`: Contains unit tests for the OPEA Reranking Microservice components
