# Reranking Microservice

The Reranking Microservice, fueled by reranking models, stands as a straightforward yet immensely potent tool for semantic search. When provided with a query and a collection of documents, reranking swiftly indexes the documents based on their semantic relevance to the query, arranging them from most to least pertinent. This microservice significantly enhances overall accuracy. In a text retrieval system, either a dense embedding model or a sparse lexical search index is often employed to retrieve relevant text documents based on the input. However, a reranking model can further refine this process by rearranging potential candidates into a final, optimized order.

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server name               |  Status   |
| ---------------------------     | --------- |
| [TEI](./impl/model_server/tei/) | &#x2713;  |
| OVMS                            | &#x2717;  |


## Configuration Options

The configuration for the Reranking Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                                |
|-----------------------------|----------------------------------------------------------------------------|
| `RERANKING_USVC_PORT`       | The port of the microservice, by default 8000                              |
| `RERANKING_SERVICE_ENDPOINT`     | The endpoint of the reranking service, e.g., "http://localhost:6060" |


## Getting started

### Prerequisite: Start Reranking Model Server
The Reranking Microservice interacts with a rerank model endpoint,  twhich must be operational and accessible at the the URL specified by the `RERANKING_SERVICE_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service.

### 🚀1. Start Reranking Microservice with Python (Option 1)

To start the Reranking microservice, you need to install python packages first.

#### 1.1. Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

#### 1.2. Start Microservice

```bash
python opea_reranking_microservice.py
```

### 🚀2. Start Retranking Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/reranking:latest -f comps/reranks/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:
```bash
docker run -d --name="reranking-microservice" \
  --net=host \
  --ipc=host \
  opea/reranking:latest
```

If the model server is running at a different URL than the default, update the `RERANKING_SERVICE_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name="reranking-microservice" \
  -e RERANKING_SERVICE_ENDPOINT=http://localhost:6060 \
  --net=host \
  --ipc=host \
  opea/reranking:latest
```

### 3. Verify the Reraniking Microservice

#### 3.1. Check Status

```bash
curl http://localhost:8000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The `top_n` parameter allows you to specify the number of results returned by the reranker model. By default, the reranker returns only the top result (top_n=1). Adding the top_n parameter enables you to retrieve multiple ranked results, with the option to adjust it as needed.

**Example Input**

```bash
curl http://localhost:8000/v1/reranking \
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}], "top_n":1}' \
  -H 'Content-Type: application/json'
```

**Example Output**

The output of the reranking microservice is a json that contains the final prompt query, constructed based on the `top_n` retrieved documents.

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

## Additional Information
### Project Structure


The project is organized into several directories:

- `impl/`: This directory contains the implementation of the supported reranking service. It includes the `model_server` directory, which contains instructions for setting up and running different model servers, for example TEI.

- `utils/`: This directory contains utility scripts and modules that are used by the Reranking Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── .env
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
  └── opea_reranking_microservice.py
```

#### Tests
- `src/tests/unit/rerankers/`: Contains unit tests for the Reranking Microservice components
