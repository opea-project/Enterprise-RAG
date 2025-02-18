# Enterprise RAG Enhanced DataPrep

## Requirements

- Python >=3.12 is required to run EDP.
- A stand alone `redis` server for task management is required.
- A stand alone `redis search` server for VectorDB data is required.
- A stand alone `postgresql` server for storing file and link entries is required.
- A stand alone `minio` server for storing files.
- Running application server:
    - backend app - application for file management
    - celery - background task management
    - (optional) flower - web ui for celery tasks

## Setup

### Environment variables

If you want to utilize all functionality, depeding on the application server you have to provide these environment variables:

| Service | Environment Variable | Description |
|---------|----------------------|-------------|
| Celery  | MINIO_BASE_URL       | Base URL for MinIO server |
|         | MINIO_ACCESS_KEY     | Access key for MinIO server |
|         | MINIO_SECRET_KEY     | Secret key for MinIO server |
|         | CELERY_BROKER_URL    | URL for Celery broker |
|         | CELERY_BACKEND_URL   | URL for Celery backend |
|         | DATAPREP_ENDPOINT    | Endpoint for data preparation service |
|         | EMBEDDING_ENDPOINT   | Endpoint for embedding service |
|         | INGESTION_ENDPOINT   | Endpoint for ingestion service |
|         | DATABASE_HOST        | Host for PostgreSQL database |
|         | DATABASE_PORT        | Port for PostgreSQL database |
|         | DATABASE_NAME        | Name of PostgreSQL database |
|         | DATABASE_USER        | User for PostgreSQL database |
|         | DATABASE_PASSWORD    | Password for PostgreSQL database |
| Flower  | CELERY_BROKER_URL    | URL for Celery broker |
|         | CELERY_BACKEND_URL   | URL for Celery backend |
|         | DATABASE_HOST        | Host for PostgreSQL database |
|         | DATABASE_PORT        | Port for PostgreSQL database |
|         | DATABASE_NAME        | Name of PostgreSQL database |
|         | DATABASE_USER        | User for PostgreSQL database |
|         | DATABASE_PASSWORD    | Password for PostgreSQL database |
| Backend | CELERY_BROKER_URL    | URL for Celery broker |
|         | CELERY_BACKEND_URL   | URL for Celery backend |
|         | DATABASE_HOST        | Host for PostgreSQL database |
|         | DATABASE_PORT        | Port for PostgreSQL database |
|         | DATABASE_NAME        | Name of PostgreSQL database |
|         | DATABASE_USER        | User for PostgreSQL database |
|         | DATABASE_PASSWORD    | Password for PostgreSQL database |
|         | MINIO_BASE_URL       | Base URL for MinIO server |
|         | MINIO_EXTERNAL_URL   | External URL for MinIO server |
|         | MINIO_ACCESS_KEY     | Access key for MinIO server |
|         | MINIO_SECRET_KEY     | Secret key for MinIO server |

### Install dependencies

To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project app/pyproject.toml
source app/.venv/bin/activate
```

### Docker images

There is a Dockerfile attached that is used to build the application server. One image is used for three application services: backend, flower, celery.

To build the application, run:
```bash
cd ../.. # src/ directory
docker build -f edp/Dockerfile -t opea/enhanced_dataprep .
```

## Running on localhost via python

To run the backend application only, use the following command:

```bash
python src/edp/app/main.py
```

## Running on localhost via Docker

To run the application servers run the following commands:

```bash
docker run -d --name edp-backend -p 5000:5000 opea/enhanced_dataprep python main.py
docker run -d --name edp-celery opea/enhanced_dataprep celery -A app.tasks.celery worker --loglevel=debug --concurrency=2
docker run -d --name edp-flower -p 5555:5555 opea/enhanced_dataprep celery -A tasks.celery flower
```

Remember to attach proper .env values for each container and ensure that you have other required services running and discoverable on network.

## Running on kubernetes

Kubernetes helm chart is stored in `deployment/edp/helm` directory. To deploy the application run:

```bash
helm repository update
helm install
```

This will deploy the application.

To get access to the Celery Web Interface run the following command:
```
kubectl port-forward --namespace edp svc/edp-flower 5555:5555
```
And proceed to the following url `http://localhost:5555`.

To get access to the `Swagger Web UI` API documentation, please run:
```
kubectl port-forward --namespace edp svc/edp-backend 1234:5000
```
And proceed to the following url `http://localhost:1234/docs`

## Testing

This application has unit tests written in `pytest`. Install it using `pip` since this is not a requirement for production.

```bash
pip install -i pytest coverage
```

Then run the following commands:

```bash
cd src/edp/tests
coverage run -m pytest
coverage report
coverage html
```

This will run the tests and create a code coverage report.
