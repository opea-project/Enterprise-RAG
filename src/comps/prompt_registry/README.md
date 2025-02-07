# Prompt Registry Microservice

Prompt Registry microservice is responsible for storing and retrieving prompts by interfacing with a MongoDB database. It includes the necessary scripts, configurations, and utilities to manage prompt data efficiently.

## Configuration options

Configuration is done by specifing MongoDB connection details. Optionally, you can specify microservice's port.

| Environment Variable    | Default Value     | Description |
|-------------------------|-------------------|-------------|
| `PROMPT_REGISTRY_MONGO_HOST` | `127.0.0.1` | MongoDB host |
| `PROMPT_REGISTRY_MONGO_PORT` | `27017` | MongoDB port |
| `PROMPT_REGISTRY_USVC_PORT` | `None` | (Optional) Microservice port |

## Getting started
### Prerequisites

To run this microservice, MongoDB database should be already running. To run the database you can use sample docker-compose file [located here](./impl/database/mongo).

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**

### Running the microservice via Python (Option 1)

If running locally, install python requirements:

```bash
pip install -r impl/microservice/requirements.txt
```

Then start the microservice:

```bash
python opea_prompt_registry_microservice.py
```

### Running the microservice via Docker (Option 2) **(recommended)**

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t promptregistry_usvc:latest -f comps/prompt_registry/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name=promptregistry-microservice --env-file comps/prompt_registry/impl/microservice/.env --network=host promptregistry_usvc:latest
```

### Example API Requests

Once prompt_registry service is up and running, users can access the database by using API endpoint below. Each API serves different purpose and return appropriate response. Prompt Registry microservice as an input accepts a json and returs a json.

#### Health Check

```bash
curl http://localhost:6012/v1/health_check  \
  -X GET                                    \
  -H 'Content-Type: application/json'
```

#### Get request

There are several possible requests that could be performed to retrieve prompts from the database:

- Retrieve all prompts from the database

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{}'
```

- Retrieve a prompt based on its id

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "prompt_id":"66f19e3dd938ac63a8e72e8f" }'
```

- Retrieve prompts based on provided filename

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "filename": "test.txt" }'
```

- Retrieve prompts based on provided text

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "prompt_text": "What is AMX" }'
```

- Retrieve prompts based on provided filename and text

```bash
curl -X 'POST'                                  \
  http://localhost:6012/v1/prompt_registry/get  \
  -H 'accept: application/json'                 \
  -H 'Content-Type: application/json'           \
  -d '{ "filename": "test2.txt", "prompt_text": "What is AMX" }'
```

If prompts are retrieved successfully, an example output will look as follows:

```bash
{
  "id":"fb97366edb5096e66e852e264d09bfed",
  "prompts":[
    {
      "id":"c6c22dd00368f413c51557310a86a6f4",
      "filename":"test.txt",
      "prompt_id":"66f19e3dd938ac63a8e72e8d",
      "prompt_text":"What is AMX?"
    },
    {
      "id":"d3c22dd00368f529c51557310a86a6g8",
      "filename":"test.txt",
      "prompt_id":"15f19e3dd938a63a8e72ee92",
      "prompt_text":"What is AMX and why is AMX?"
    },
    {
      "id":"7d2fdad3dc6e05d6b492448c4a8762ec",
      "filename":"test2.txt",
      "prompt_id":"66f19e3dd938ac63a8e72e91",
      "prompt_text":"What is AMX and how?"
    }
  ]
}
```

#### Create request

Create endpoint accepts `prompt_text` and `filename` as inputs.
Example request looks as follows:

```bash
curl -X 'POST'                                      \
  http://localhost:6012/v1/prompt_registry/create   \
  -H 'accept: application/json'                     \
  -H 'Content-Type: application/json'               \
  -d '{ "prompt_text": "test prompt", "filename": "test" }'
```

If a prompt is added successfully, an example output will look as follows:

```bash
{"id":"1521111186d5f72a762acf3cdc5e564f","prompt_id":"66f2c021e9c8144058413159"}
```

#### Delete request

Delete endpoint accepts a `prompt_id` provided for the prompt that should be deleted. Example request looks as follows:

```bash
curl -X 'POST' \
  http://localhost:6012/v1/prompt_registry/delete \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "prompt_id":"66f1689ae3995e5691dc1110"}'
```

If the prompt is deleted successfully, the response will not return any output, but the returned status code will be `200`.

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the prompt registry service.
- `utils/`: This directory contains scripts that are used by the Prompt Registry Microservice.

The tree view of the main directories and files:

```bash
├── README.md
├── impl
│   ├── database
│   │   └── mongo
│   │       └── docker-compose.yaml
│   │       └── README.md
│   └── microservice
│       ├── .env
│       ├── Dockerfile
│       └── requirements.txt
├── opea_prompt_registry_microservice.py
└── utils
    ├── documents.py
    └── opea_prompt_registry.py

```