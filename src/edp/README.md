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
If the S3 compatible endpoint does not support bucket notifications, files uploaded to the storage will not appear in EDP database and will not be visible in the UI. Data will also not be processed and available in the vector database of choice. To overcome this, a pulling synchronization option is available. To use it, edit the `deployment/components/edp/values.yaml` file and set the `celery.config.scheduledSync.enabled` to `true`. Optionally configure the pulling frequency by setting the `celery.config.scheduledSync.syncPeriodSeconds` - set the number of seconds between each pull request from storage. Note that for storages with high amount of files and/or frequently changed files requires more delay between each subsequent pulls. For small amount of files this option can be set to a lower value, such as "60" seconds. Sample configuration that enables scheduled synchronization:

```yaml
celery:
  config:
    scheduledSync:
      enabled: true
      syncPeriodSeconds: "60"
```

You can also manually schedule the synchronization task. To run the synchronization task perform a request to either:
- `POST /api/files/sync/` to backend container form within the cluster.
- `POST /api/v1/edp/files/sync` to WebUI - this requires passing `Authorization` token.

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

| Service | Environment Variable       | Description |
|---------|----------------------------|--------------------------|
| Celery  | EDP_EXTERNAL_URL           | Base URL for External S3 endpoint, assumes http:// schema if not defined in the url |
|         | EDP_INTERNAL_URL           | Base URL for Internal S3 endpoint, assumes http:// schema if not defined in the url |
|         | EDP_EXTERNAL_CERT_VERIFY   | Should EDP verify the external S3 endpoint certificate validity |
|         | EDP_INTERNAL_CERT_VERIFY   | Should EDP verify the internal S3 endpoint certificate validity |
|         | EDP_BASE_REGION            | Base region for EDP S3 buckets |
|         | EDP_SYNC_TASK_TIME_SECONDS | If defined and not empty, will enable Celery's periodic task to pull changes from storage |
|         | MINIO_ACCESS_KEY           | Access key either to MinIO or S3 IAM user |
|         | MINIO_SECRET_KEY           | Secret key either to MinIO or S3 IAM user |
|         | BUCKET_NAME_REGEX_FILTER   | Regex filter for filtering out available buckets by name |
|         | CELERY_BROKER_URL          | URL for Celery broker |
|         | CELERY_BACKEND_URL         | URL for Celery backend |
|         | DATAPREP_ENDPOINT          | Endpoint for data preparation service |
|         | EMBEDDING_ENDPOINT         | Endpoint for embedding service |
|         | INGESTION_ENDPOINT         | Endpoint for ingestion service |
|         | DATABASE_HOST              | Host for PostgreSQL database |
|         | DATABASE_PORT              | Port for PostgreSQL database |
|         | DATABASE_NAME              | Name of PostgreSQL database |
|         | DATABASE_USER              | User for PostgreSQL database |
|         | DATABASE_PASSWORD          | Password for PostgreSQL database |
| Flower  | CELERY_BROKER_URL          | URL for Celery broker |
|         | CELERY_BACKEND_URL         | URL for Celery backend |
|         | DATABASE_HOST              | Host for PostgreSQL database |
|         | DATABASE_PORT              | Port for PostgreSQL database |
|         | DATABASE_NAME              | Name of PostgreSQL database |
|         | DATABASE_USER              | User for PostgreSQL database |
|         | DATABASE_PASSWORD          | Password for PostgreSQL database |
| Backend | CELERY_BROKER_URL          | URL for Celery broker |
|         | CELERY_BACKEND_URL         | URL for Celery backend |
|         | DATABASE_HOST              | Host for PostgreSQL database |
|         | DATABASE_PORT              | Port for PostgreSQL database |
|         | DATABASE_NAME              | Name of PostgreSQL database |
|         | DATABASE_USER              | User for PostgreSQL database |
|         | DATABASE_PASSWORD          | Password for PostgreSQL database |
|         | EDP_EXTERNAL_URL           | Base URL for External S3 endpoint |
|         | EDP_INTERNAL_URL           | Base URL for Internal S3 endpoint |
|         | EDP_EXTERNAL_CERT_VERIFY   | Should EDP verify the external S3 endpoint certificate validity |
|         | EDP_INTERNAL_CERT_VERIFY   | Should EDP verify the internal S3 endpoint certificate validity |
|         | EDP_BASE_REGION            | Base region for EDP S3 buckets |
|         | MINIO_ACCESS_KEY           | Access key either to MinIO or S3 IAM user |
|         | MINIO_SECRET_KEY           | Secret key either to MinIO or S3 IAM user |
|         | BUCKET_NAME_REGEX_FILTER   | Regex filter for filtering out available buckets by name |
| Sqs     | AWS_SQS_EVENT_QUEUE_URL    | AWS SQS Queue url to listen for S3 events |
|         | EDP_BACKEND_ENDPOINT       | Endpoint to backend service |
|         | AWS_DEFAULT_REGION         | Base region for EDP S3 buckets |
|         | AWS_ACCESS_KEY_ID          | Access key to S3 IAM user |
|         | AWS_SECRET_ACCESS_KEY      | Secret key to S3 IAM user |

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

## Troubleshooting

### My selected S3 or S3-Compatible storage does not support bucket notifications
If you are unable to use bucket notifications through the `minio-event` URL or use `aws-sqs`, you will not receive notifications of file changes from your storage. To mitigate this, you have the option of manual or scheduled sync. Manual sync can be performed by sending a `POST /api/v1/edp/files/sync` request, which queries the storage buckets and compares them to the data in the EDP database. You can also perform a differential query without synchronization tasks by sending a `GET /api/v1/edp/files/sync` request. This will return a JSON array containing status of all files - either to be added, deleted, updated or skipped. Additionally, you can configure a scheduled sync job to perform the sync task at regular intervals. To set this up, configure the `celery.config.scheduledSync` options in the Helm chart (deployment/components/edp/values.yaml) by enabling it and configuring the synchronization period.

### File upload certificate error
If you deployed ERAG with self-signed certificates, you might also need to accept the external storage certificate. Web browsers require acceptance of certificates for each domain they encounter, even if these are self-signed wildcard certificates. Therefore, you must accept certificates for both your Web GUI and the S3 endpoint. For instance, if your GUI is running under myrag.example.com and the storage is configured at s3.myrag.example.com, you need to visit both domains directly and accept their self-signed certificates. Alternatively, you can upload the self-signed certificates to your browser's certificate store.

### Protocol missmatch
If you encounter a protocol mismatch error, it may be because edpExternalUrl has different schema than ERAG schema. For example, if your ERAG is at https://myrag.example.com and you set edpExternalUrl to http://s3.example.com, this will generate a presigned URL with an HTTP schema, resulting in a protocol mismatch error on a https secured Web UI.

### CORS related issues
Your chosen S3 storage endpoint can be configured with special settings known as CORS (Cross-Origin Resource Sharing). When you upload a file using the EDP web GUI, your browser requests a presigned URL from the backend. This URL enables you to upload files to S3-compatible storage without needing to provide credentials. However, this URL will not match the current URL of the EDP GUI you are using. For instance, if your GUI is running under myrag.example.com and the storage is configured at storage.mycorp.internal, you will encounter a CORS error. This occurs because your browser and the storage endpoint do not permit requests from unapproved origins. To resolve this issue, ensure that the storage is properly configured to allow your origin. In the example above, the CORS configuration on your chosen storage should permit requests from myrag.example.com. For more details on CORS, please refer to the manufacturer's documentation.

### PostgreSQL connection errors
Make sure that PostgreSQL initialization process was successfull. This container should not have restarted when deploying the solution. Ensure that output logs from the deployment contain following lines:
```
Creating user edp
Granting access to "edp" to the database "edp"
```
This ensures that the database and users were initialized successfully. If the database container was restarted, check the container events and look for readinessProbe events. If the initialization process is taking long, this probe might restart the container, interrupting the initializaton process. This will result in connections errors such as:
```
FATAL:  password authentication failed for user "edp"
DETAIL:  Role "edp" does not exist.
```
This indicated the PostgreSQL database was not initialized properly.

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

### Testing S3 Compatible

Run a simple S3 mock server. Port 9191 will be used to expose a https server with self-signed certificate.

```bash
docker run --rm -p 9191:9191 -e initialBuckets=default,secondary -t adobe/s3mock
```

Export EDP confgiuration:

```bash
export edp_storage_type="s3compatible"
export s3_access_key="testtesttest"
export s3_secret_key="testtesttest"
export s3_compatible_endpoint="https://<your IP address here>:9191/"
export s3_region="us-east-1"
export s3_bucket_name_regex_filter=".*"
export s3_cert_verify="false"
```

As this endpoint does not have event notifications built in, enable scheduled sync. Edit `deployment/components/edp/values.yaml` and set the following values:
```yaml
celery:
  config:
    scheduledSync:
      enabled: true
      syncPeriodSeconds: "60"
```

Then deploy using `install_chatqna.sh` depending on the deployment type you're using. Example for development:
```bash
./install_chatqna.sh --auth --deploy examples/cpu-torch.yaml --ui --kind
```

After successful deployment, upload files using either WebGUI or cURL:

```bash
curl -X PUT "https://localhost:9191/default/test.txt" --upload-file test.txt -H "Content-Type: application/octet-stream" -k
```
