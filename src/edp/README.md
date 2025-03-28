# Enterprise RAG Enhanced DataPrep

## Requirements

- Python >=3.12 is required to run EDP.
- A stand alone `redis` server for task management is required.
- A stand alone `redis search` server for VectorDB data is required.
- A stand alone `postgresql` server for storing file and link entries is required.
- A S3 compatible storage (one of the following)
    - A stand alone `minio` server for storing files. This is included and optional.
    - An external AWS S3 bucket. Example scripts for creating one are located in terraform directory.
    - External server compatible with S3 API

- Running application server:
    - backend - application for file management
    - celery - background task management
    - (optional) flower - web ui for celery tasks
    - (optional) sqs - queue listener for S3 events if using AWS S3

### Storage endpoints

Currently, EDP allows using the following storage backends for storing and processing files from.

#### Internal MinIO storage server (default)
If using minio storage, MinIO server will be automatically deployed and configured. Minio is used if not overriden by `edp_storage_type` env variable while running `install_chatqna.sh`.

#### AWS S3 storage
For requirements for using S3 storage with this software, please refer to the [terraform README.md](terraform/README.md) for more details and installation instructions.

For example:
```
export edp_storage_type="s3"            # This will choose S3 as storage type for EDP
export s3_access_key=""                 # IAM access key which will be used to communicate with AWS
export s3_secret_key=""                 # IAM secret key which will be used to communicate with AWS
export s3_sqs_queue=""                  # AWS SQS endpoint URI that will be used for retrieving bucket/object notificiations
export s3_region="us-east-1"            # (optional) AWS Region for buckets
export s3_bucket_name_regex_filter=".*" # (optional) Filter bucket names to display in WebUI

cd deployment
./install_chatqna.sh <command options>
```

#### S3 API compatible storage
To use external storage server that is compatible with S3 API, follow similar steps as in the above AWS S3 storage with substitution to your endpoint settings.

For example:
```
export edp_storage_type="s3compatible"  # This will choose S3 as storage type for EDP
export s3_access_key=                   # S3 compatible storage access key
export s3_secret_key=                   # S3 compatible storage secret key
export s3_compatible_endpoint=          # S3 compatible storage endpoint
export s3_region=""                     # (optional) Region if it is required by the S3 compatible storage
export s3_bucket_name_regex_filter=".*" # (optional) Filter bucket names to display in WebUI

cd deployment
./install_chatqna.sh <command options>
```

## Setup

### Environment variables

If you want to utilize all functionality, depeding on the application server you have to provide these environment variables:

| Service | Environment Variable     | Description |
|---------|--------------------------|--------------------------|
| Celery  | EDP_EXTERNAL_URL         | Base URL for External S3 endpoint |
|         | EDP_INTERNAL_URL         | Base URL for Internal S3 endpoint |
|         | EDP_EXTERNAL_SECURE      | Should EDP use secure connection to external S3 endpoint |
|         | EDP_INTERNAL_SECURE      | Should EDP use secure connection to internal S3 endpoint |
|         | EDP_BASE_REGION          | Base region for EDP S3 buckets |
|         | MINIO_ACCESS_KEY         | Access key either to MinIO or S3 IAM user |
|         | MINIO_SECRET_KEY         | Secret key either to MinIO or S3 IAM user |
|         | CELERY_BROKER_URL        | URL for Celery broker |
|         | CELERY_BACKEND_URL       | URL for Celery backend |
|         | DATAPREP_ENDPOINT        | Endpoint for data preparation service |
|         | EMBEDDING_ENDPOINT       | Endpoint for embedding service |
|         | INGESTION_ENDPOINT       | Endpoint for ingestion service |
|         | DATABASE_HOST            | Host for PostgreSQL database |
|         | DATABASE_PORT            | Port for PostgreSQL database |
|         | DATABASE_NAME            | Name of PostgreSQL database |
|         | DATABASE_USER            | User for PostgreSQL database |
|         | DATABASE_PASSWORD        | Password for PostgreSQL database |
| Flower  | CELERY_BROKER_URL        | URL for Celery broker |
|         | CELERY_BACKEND_URL       | URL for Celery backend |
|         | DATABASE_HOST            | Host for PostgreSQL database |
|         | DATABASE_PORT            | Port for PostgreSQL database |
|         | DATABASE_NAME            | Name of PostgreSQL database |
|         | DATABASE_USER            | User for PostgreSQL database |
|         | DATABASE_PASSWORD        | Password for PostgreSQL database |
| Backend | CELERY_BROKER_URL        | URL for Celery broker |
|         | CELERY_BACKEND_URL       | URL for Celery backend |
|         | DATABASE_HOST            | Host for PostgreSQL database |
|         | DATABASE_PORT            | Port for PostgreSQL database |
|         | DATABASE_NAME            | Name of PostgreSQL database |
|         | DATABASE_USER            | User for PostgreSQL database |
|         | DATABASE_PASSWORD        | Password for PostgreSQL database |
|         | EDP_EXTERNAL_URL         | Base URL for External S3 endpoint |
|         | EDP_INTERNAL_URL         | Base URL for Internal S3 endpoint |
|         | EDP_EXTERNAL_SECURE      | Should EDP use secure connection to external S3 endpoint |
|         | EDP_INTERNAL_SECURE      | Should EDP use secure connection to internal S3 endpoint |
|         | EDP_BASE_REGION          | Base region for EDP S3 buckets |
|         | MINIO_ACCESS_KEY         | Access key either to MinIO or S3 IAM user |
|         | MINIO_SECRET_KEY         | Secret key either to MinIO or S3 IAM user |
|         | BUCKET_NAME_REGEX_FILTER | Regex filter for filtering out available buckets by name |
| Sqs     | AWS_SQS_EVENT_QUEUE_URL  | AWS SQS Queue url to listen for S3 events |
|         | EDP_BACKEND_ENDPOINT     | Endpoint to backend service |
|         | AWS_DEFAULT_REGION       | Base region for EDP S3 buckets |
|         | AWS_ACCESS_KEY_ID        | Access key to S3 IAM user |
|         | AWS_SECRET_ACCESS_KEY    | Secret key to S3 IAM user |

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
