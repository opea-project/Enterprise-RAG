# System Fingerprint Microservice

The System Fingerprint microservice is responsible for generating and managing unique fingerprints for different systems and giving user ability to store and update component arguments. It includes the necessary scripts, configurations, and utilities to efficiently handle fingerprint data.

## Configuration options

Configuration is done by specifying the MongoDB connection details. Optionally, you can specify the microservice's port.

| Environment Variable    | Default Value     | Description |
|-------------------------|-------------------|-------------|
| `SYSTEM_FINGERPRINT_MONGODB_HOST` | `127.0.0.1` | MongoDB host |
| `SYSTEM_FINGERPRINT_MONGODB_PORT` | `27017` | MongoDB port |
| `MONGODB_NAME` | `SYSTEM_FINGERPRINT` | Name of MongoDB |
| `SYSTEM_FINGERPRINT_USVC_PORT` | `6012` | (Optional) Microservice port |

## Getting started
### Prerequisites

To run this microservice, the MongoDB database should already be running. To run the database, you can use [the sample docker-compose file](./impl/database/mongo).

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**

### Running the microservice via Python (Option 1)

If running locally, install the Python requirements:

```bash
pip install -r impl/microservice/requirements.txt
```

Then start the microservice:

```bash
python system_fingerprint_microservice.py
```

### Running the microservice via Docker (Option 2) **(recommended)**

Using a container is the preferred way to run the microservice.

#### Build the Docker service

Navigate to the `src` directory and use the Docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t systemfingerprint_usvc:latest -f comps/system_fingerprint/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by using the `-e` option with the Docker run command, such as the vector database configuration and database endpoint.

```bash
docker run -d --name=systemfingerprint-microservice --env-file comps/system_fingerprint/impl/microservice/.env --network=host systemfingerprint_usvc:latest
```
### Example API Requests

Once the System Fingerprint service is up and running, users can access the database using the following API endpoint. Each API serves a different purpose and returns an appropriate response. The System Fingerprint microservice accepts JSON as input and returns JSON.

#### Health Check

To perform a health check, use the following command:

```bash
curl http://localhost:6012/v1/health_check  \
  -X GET                                    \
  -H 'Content-Type: application/json'
```

#### Change arguments

This endpoint allows you to change arguments and store them in MongoDB. It accepts input in the following format:

```python
List[ComponentArgument]
```

Where `ComponentArgument` is defined as:

```python
class ComponentArgument(BaseDoc):
    name: str
    data: dict
```

Example curl command:

```bash
curl -X POST http://localhost:6012/v1/system_fingerprint/change_arguments \
-H "Content-Type: application/json" \
-d '[
    {
        "name": "llm",
        "data": {
            "max_new_tokens": 1024,
            "top_k": 10
        }
    }
]'
```

A full set of possible configurations can be found in the file [object_document_mapper.py](utils/object_document_mapper.py).

#### Append arguments

This endpoint accepts input as a dictionary and appends up-to-date arguments based on records in MongoDB. 

Example curl command:

```bash
curl -X POST http://localhost:6012/v1/system_fingerprint/append_arguments \
-H "Content-Type: application/json" \
-d '{
    "text": "What is AMX?"
}'
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the System Fingerprint service.
- `utils/`: This directory contains scripts that are used by the System Fingerprint Microservice.

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
├── system_fingerprint_microservice.py
└── utils
    ├── object_document_mapper.py
    └── system_fingerprint.py
