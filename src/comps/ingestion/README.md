# Ingestion Microservice

This service allows multiple services to ingest data into a vector database.

## Configuration options

Configuration is done by selecting the desired vector store type. In addition, the specific vector store endpoint connections settings have to be passed.  For more information on selecting proper vector database and usage please refer to [VectorStore documentation](../vectorstores/README.md).

| Environment Variable    | Default Value     | Description                                                                                      |
|-------------------------|-------------------|--------------------------------------------------------------------------------------------------|
| `VECTOR_STORE`          | `redis`           | Vector Store database type                                                                       |

### Vector Store Support Matrix

Support for specific vector databases:

| Vector Database                             |  Status   |
| --------------------------------------------| --------- |
| [REDIS](../vectorstores/README.md#redis)    | &#x2713;  |
| [MILVUS](../vectorstores/README.md#milvus)  | &#x2717;  |
| [QDRANT](../vectorstores/README.md#qdrant)  | &#x2717;  |

## Getting started

Since this service is utilizing VectorStore code, you have to configure the underlying implementation by setting an env variable `VECTOR_STORE` along with vector database configuration for the selected endpoint.

We offer 2 ways to run this microservice: 
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**

### Prerequisites

To run this microservice, a vector database should be already running. To run one of the [supported vector](#vector-store-support-matrix) databases you can use sample docker-compose files [located here](../vectorstores/impl/).

### Running the microservice via Python (Option 1)

If running locally, install python requirements:

```bash
pip install -r impl/microservice/requirements.txt
```

Then start the microservice:

```bash
python opea_ingestion_microservice.py
```

This sample assumes redis as a vector store database. You can run it by [following this documentation](../vectorstores/README.md#redis).

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/ingestion:latest -f comps/ingestion/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name="ingestion" --env-file comps/ingestion/impl/microservice/.env -p 6120:6120 opea/ingestion:latest
```

### Example input

```bash
  curl http://localhost:6120/v1/ingestion \
    -X POST \
    -d '{ docs: [ { "text": "What is Intel AVX-512?", "embedding": [1,2,3] } ] }' \
    -H 'Content-Type: application/json'
```
### Example output

Output data, if the request is successfull, is equal to input data.

```json
{
  "docs": [
    {
      "text": "What is Intel AVX-512?", 
      "embedding": [1, 2, 3]
    }
  ]
}
```

## Additional Information
   
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the ingestion service.

- `utils/`: This directory contains scripts that are used by the Ingestion Microservice.

The tree view of the main directories and files:

```bash
.
├── impl
│   └── microservice
│       ├── Dockerfile
│       └── requirements.txt
|       └── .env
├── opea_ingestion_microservice.py
├── README.md
└── utils
    ├── opea_ingestion.py
```
