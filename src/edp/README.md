# Enterprise RAG Enhanced DataPrep Service

The OPEA ERAG Enhanced Data Preparation (EDP) service provides advanced document processing capabilities for the Enterprise RAG system, ensuring automated data flow from storage to retriever-ready format. The service supports multiple storage backends for managing and processing documents: `MinIO`, `AWS S3`, and `S3-compatible` endpoints.

## Table of Contents

- [Requirements](#requirements)
- [Configuration](#configuration)
  - [Storage endpoints](#storage-endpoints)
- [Storage Synchronization](#storage-synchronization)
- [RBAC (Role-Based Access Control)](#rbac-role-based-access-control)
- [Setup](#setup)
  - [Environment variables](#environment-variables)
  - [Install dependencies](#install-dependencies)
  - [Docker images](#docker-images)
- [Running on localhost via python](#running-on-localhost-via-python)
- [Running on localhost via Docker](#running-on-localhost-via-docker)
- [Running on kubernetes](#running-on-kubernetes)
- [Troubleshooting](#troubleshooting)
  - [My selected S3 or S3-Compatible storage does not support bucket notifications](#my-selected-s3-or-s3-compatible-storage-does-not-support-bucket-notifications)
  - [File upload certificate error](#file-upload-certificate-error)
  - [Protocol mismatch](#protocol-mismatch)
  - [CORS related issues](#cors-related-issues)
  - [PostgreSQL connection errors](#postgresql-connection-errors)
- [Testing](#testing)
  - [Testing S3 Compatible](#testing-s3-compatible)
- [Development](#development)

## Requirements

- Python >=3.11 is required to run EDP.
- A stand alone `redis` server for task management is required.
- A stand alone `redis search` server or Redis >= 8.0 for VectorDB data is required.
- A stand alone `postgresql` server for storing file and link entries is required.
- A S3 compatible storage (one of the following)
    - A stand alone `MinIO` server for storing files. This is included and optional.
    - An external AWS S3 bucket. Example scripts for creating one are located in terraform directory - see [terraform/README.md](terraform/README.md).
    - External server compatible with the S3 API

- Running application server:
    - backend - application for file management
    - celery - background task management
    - (optional) flower - web ui for celery tasks
    - (optional) sqs - queue listener for S3 events if using AWS S3


## Configuration

Similar to other Enterprise RAG components, EDP has its own section under the deployment [config.yaml](../../deployment/inventory/sample/config.yaml). All possible configuration options are listed in [deployment/components/edp/values.yaml](../../deployment/components/edp/values.yaml).

### Storage endpoints
Use the config.yaml file to define the storage backend. Set the desired `storageType` under the edp section in your config.yaml, see [inventory/sample/config.yaml](../../deployment/inventory/sample/config.yaml). Then, configure the appropriate sub-section based on the selected type.

#### Internal MinIO Storage (default)
This will deploy and use the bundled MinIO instance:
```yaml
edp:
  enabled: true
  storageType: minio
  minio:
    domainName: minio.erag.com
    apiDomainName: s3.erag.com
    bucketNameRegexFilter: ".*"
```

#### AWS S3 Storage
To connect to AWS S3, set the storage type to s3 and provide your credentials and configuration:

```yaml
edp:
  enabled: true
  storageType: s3
  s3:
    accessKey: "<your-aws-access-key>"
    secretKey: "<your-aws-secret-key>"
    region: "us-east-1"
    sqsQueue: "<optional-sqs-endpoint-uri>"
    bucketNameRegexFilter: ".*"
```

To see example scripts for creating required AWS resources such as S3 buckets and SQS queues, refer to the [terraform/README.md](terraform/README.md).

Optionally, the environment variables (using the same names as in the legacy bash-based deployment, such as `edp_storage_type`, `s3_access_key`, `s3_secret_key`, etc.) can be exported instead of using config.yaml. However, defining configuration in the YAML file is preferred for clarity, consistency, and better integration with automated Ansible-based deployments.

#### S3 API Compatible Storage
To use other storage server that is compatible with S3 API, follow similar steps as in the above AWS S3 storage with substitution to your s3-compatible endpoint settings:

```yaml
edp:
  enabled: true
  s3compatible:
    region: "<optional, required if your storage enforces region settings>"
    accessKeyId: "<your-access-key>"
    secretAccessKey: "<your-secret-key>"
    internalUrl: "https://s3.example.com"
    externalUrl: "https://s3.example.com"
    bucketNameRegexFilter: ".*"
```

Optionally, the environment variables (using the same names as in the legacy bash-based deployment, such as `edp_storage_type`, `s3_compatible_endpoint`, `s3_access_key`, `s3_secret_key`, etc.) can be exported instead of using config.yaml. However, defining configuration in the YAML file is preferred for clarity, consistency, and better integration with automated Ansible-based deployments.

> [!NOTE]
> If your S3-compatible backend does not support bucket event notifications, you must enable scheduled or manual synchronization. See the [Storage Synchronization section](#storage-synchronization) for instructions.

Then deploy the application by following the instructions in [deployment/README.md](../../deployment/README.md). Example for installation:
```bash
ansible-playbook playbooks/application.yaml --tags install -e @path/to/your/config.yaml
```

After successful deployment, upload files using either WebGUI or cURL:

```bash
curl -X PUT "https://localhost:9191/default/test.txt" --upload-file test.txt -H "Content-Type: application/octet-stream" -k
```

## Storage Synchronization
If the configured S3-compatible storage does not support bucket notifications, files uploaded to the storage will not be automatically registered in the EDP database, and they won't be visible in the ERAG UI.

To address this limitation, Enterprise DataPrep provides a pull-based synchronization mechanism. When enabled, it periodically scans the configured storage and updates the internal database accordingly.

To use it, edit the [deployment/components/edp/values.yaml](../../deployment/components/edp/values.yaml) file and set the `celery.config.scheduledSync.enabled` to `true`.

Pulling frequency can by adjusted by setting the `celery.config.scheduledSync.syncPeriodSeconds` - set the number of seconds between each pull request from storage. Note that for storages with high amount of files and/or frequently changed files requires more delay between each subsequent pulls, so consider increasing this value to reduce load. For small datasets, lower values (e.g., 60 seconds) are acceptable.

Sample configuration that enables scheduled synchronization:

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

## RBAC (Role-Based Access Control)

RBAC in EDP is implemented to manage and restrict access to data based on roles and permissions. The following outlines four distinct RBAC modes, each with its own approach to access control:

### 1. None
- **Description**: No access control policies are enforced.
- **Implementation**: This mode bypasses RBAC entirely, granting unrestricted access to all data.
- **Use Case**: Suitable for scenarios where data access restrictions are unnecessary, such as testing or environments where security is not a concern.

### 2. Always
- **Description**: Access is verified for every request.
- **Implementation**:
  - Every data access request is sent to an external security provider for validation.
  - The security provider checks the user's role and permissions against the latest mappings.
- **Trade-offs**:
  - **Pros**: Ensures the most up-to-date access control.
  - **Cons**: Adds latency to the data pipeline due to frequent external requests.
- **Use Case**: Ideal for environments requiring strict and real-time access control.

### 3. Cached
- **Description**: Combines external validation with caching for improved performance.
- **Implementation**:
  - The first request for a resource is validated by the external security provider.
  - Subsequent requests use cached responses, with a Time-To-Live (TTL) expiration to ensure periodic updates.
- **Trade-offs**:
  - **Pros**: Reduces latency for repeated requests.
  - **Cons**: Permission changes on the security provider may take time to reflect due to caching.
- **Use Case**: Suitable for balancing security and performance in high-traffic environments.

### 4. Static
- **Description**: Uses predefined mappings for access control. This is configured by setting the VECTOR_DB_RBAC_STATIC_CONFIG environment variable. It has to be in JSON format. It can be an array - limiting to a static list of buckets, or a dict mapped as key=user_id, value=array_of_buckets.
- **Implementation**:
  - Access is determined by static mappings of groups or buckets.
  - No external security provider is involved, and changes require manual updates.
- **Trade-offs**:
  - **Pros**: Simple and independent of external systems.
  - **Cons**: No synchronization with external changes; requires manual intervention for updates.
- **Use Case**: Best for environments with stable and predictable access requirements.

Each RBAC mode in EDP offers a different balance between security, performance, and flexibility. The choice of mode depends on the specific requirements of the environment, such as latency tolerance, frequency of permission changes, and reliance on external security providers.

RBAC usage is optional and even though configured, retrieval services are not required to use it. This provides only additional API to select limited list of bucket access.

The storage itself acts as the source of truth for access validation. This ensures that requests are validated directly against the storage's access control policies, providing a robust and consistent mechanism for enforcing permissions.

A graph showing the validation flow should look as follows:

```
   ┌───────────────┐                                                                           
   │               │                                                                           
   │ Authorization │                               ┌───────────────┐                           
   │               │                               │               │                           
   └───────┬───────┘                               │   Vector DB   │                           
           │                                       │               │                           
 Authorization Header                              └───────▲───────┘                           
           │                                               │                                   
           │                                               │6                                  
   ┌───────▼───────┐       ┌───────────────┐       ┌───────┴───────┐        ┌───────────────┐  
   │               │  ...  │               │   1   │               │   7    │               │  
   │    Step 1     ├───────►    Step 2     ├───────►   Retrieval   ├────────►    Step N     │  
   │               │       │               │       │               │        │               │  
   └───────────────┘       └───────────────┘       └───┬───────▲───┘        └───────────────┘  
                                                       │       │                               
                                                      2│       │5                              
                                                       │       │                               
                           ┌───────────────┐       ┌───▼───────┴───┐   4    ┌───────────────┐  
                           │     Cache     ◄───────┤               ◄────────┤               │  
                           │               │       │  EDP Backend  │        │  Storage API  │  
                           │  (Optional)   ├───────►               ├────────►               │  
                           └───────────────┘       └───────────────┘   3    └───────────────┘  
```

1. Request to retrieval pipeline step. If VECTOR_DB_RBAC is disabled on retriever, skip to step 7.
2. Retrieve bucket list using with read access using current Authorization header.
3. Call storage API using service key for list of available buckets. Limit it using built in regex filter. 
4. For each bucket check if user can read a random file within in that bucket using credentials based on passed Authorization header.
5. Respond with a list containing all buckets with read permission using user permissions.
6. Limit vector query scope to elements belonging to retrieved bucket list.
7. Pass filtered results further down the pipeline

## Setup

### Environment variables

If you want to utilize all functionality, depending on the application server you have to provide these environment variables:

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
|         | HIERARCHICAL_DATAPREP_ENDPOINT | Endpoint for hierarchical dataprep service |
|         | TEXT_EXTRACTOR_ENDPOINT       | Endpoint for text extractor service |
|         | TEXT_COMPRESSION_ENDPOINT | Endpoint for text compression service |
|         | TEXT_SPLITTER_ENDPOINT     | Endpoint for text splitter service |
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
|         | VECTOR_DB_RBAC                  | Set the type of RBAC bucket filtering |
|         | VECTOR_DB_RBAC_STATIC_CONFIG    | Configuration of STATIC rbac settings |
|         | VECTOR_DB_RBAC_CACHE_EXPIRATION | Configuration of entry TTL for CACHED rbac settings |
| Sqs     | AWS_SQS_EVENT_QUEUE_URL    | AWS SQS Queue url to listen for S3 events |
|         | EDP_BACKEND_ENDPOINT       | Endpoint to backend service |
|         | AWS_DEFAULT_REGION         | Base region for EDP S3 buckets |
|         | AWS_ACCESS_KEY_ID          | Access key to S3 IAM user |
|         | AWS_SECRET_ACCESS_KEY      | Secret key to S3 IAM user |

### Install dependencies

To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
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
docker network create edp-network
docker run -d --network edp-network --name edp-postgres -e POSTGRES_USER=edp -e POSTGRES_DB=enhanced_dataprep -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17
docker run -d --network edp-network --name edp-redis redis:8
docker run --rm -it --network edp-network --name edp-backend -p 5000:5000 -e DATABASE_HOST=edp-postgres -e DATABASE_USER=edp -e CELERY_BROKER_URL=redis://edp-redis:6379/0 -e CELERY_BACKEND_URL=redis://edp-redis:6379/0 opea/enhanced_dataprep
docker run -d --network edp-network --name edp-celery opea/enhanced_dataprep celery -A app.tasks.celery worker --loglevel=debug --concurrency=2
# (optional)
docker run -d --network edp-network --name edp-flower -p 5555:5555 opea/enhanced_dataprep celery -A tasks.celery flower
```

Remember to attach proper `.env` values for each container and ensure that you have other required services running and discoverable on network.

## Running on kubernetes

Kubernetes helm chart is stored in [deployment/components/edp/helm](../../deployment/components/edp) directory. To deploy the application run:

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
If you are unable to use bucket notifications through the `minio-event` URL or use `aws-sqs`, you will not receive notifications of file changes from your storage. To mitigate this, you have the option of manual or scheduled sync. Manual sync can be performed by sending a `POST /api/v1/edp/files/sync` request, which queries the storage buckets and compares them to the data in the EDP database. You can also perform a differential query without synchronization tasks by sending a `GET /api/v1/edp/files/sync` request. This will return a JSON array containing status of all files - either to be added, deleted, updated or skipped. Additionally, you can configure a scheduled sync job to perform the sync task at regular intervals. To set this up, configure the `celery.config.scheduledSync` options in the Helm chart ([deployment/components/edp/values.yaml](../../deployment/components/edp/values.yaml)) by enabling it and configuring the synchronization period. See the [Storage Synchronization section](#storage-synchronization) for instructions.

### File upload certificate error
If you deployed ERAG with self-signed certificates, you might also need to accept the external storage certificate. Web browsers require acceptance of certificates for each domain they encounter, even if these are self-signed wildcard certificates. Therefore, you must accept certificates for both your Web GUI and the S3 endpoint. For instance, if your GUI is running under myrag.example.com and the storage is configured at s3.myrag.example.com, you need to visit both domains directly and accept their self-signed certificates. Alternatively, you can upload the self-signed certificates to your browser's certificate store.

### Protocol mismatch
If you encounter a protocol mismatch error, it may be because edpExternalUrl has different schema than ERAG schema. For example, if your ERAG is at https://myrag.example.com and you set edpExternalUrl to http://s3.example.com, this will generate a presigned URL with an HTTP schema, resulting in a protocol mismatch error on a https secured Web UI.

### CORS related issues
Your chosen S3 storage endpoint can be configured with special settings known as CORS (Cross-Origin Resource Sharing). When you upload a file using the EDP web GUI, your browser requests a presigned URL from the backend. This URL enables you to upload files to S3-compatible storage without needing to provide credentials. However, this URL will not match the current URL of the EDP GUI you are using. For instance, if your GUI is running under myrag.example.com and the storage is configured at storage.mycorp.internal, you will encounter a CORS error. This occurs because your browser and the storage endpoint do not permit requests from unapproved origins. To resolve this issue, ensure that the storage is properly configured to allow your origin. In the example above, the CORS configuration on your chosen storage should permit requests from myrag.example.com. For more details on CORS, please refer to the manufacturer's documentation.

### PostgreSQL connection errors
Make sure that PostgreSQL initialization process was successful. This container should not have restarted when deploying the solution. Ensure that output logs from the deployment contain following lines:
```
Creating user edp
Granting access to "edp" to the database "edp"
```
This ensures that the database and users were initialized successfully. If the database container was restarted, check the container events and look for readinessProbe events. If the initialization process is taking long, this probe might restart the container, interrupting the initialization process. This will result in connections errors such as:
```
FATAL:  password authentication failed for user "edp"
DETAIL:  Role "edp" does not exist.
```
This indicates the PostgreSQL database was not initialized properly.

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

### PresignedUrl generation

EDP generates presigned URLs that allows users to upload, download, or delete files via WebUI or directly through the S3 endpoint. By default, these URLs are created using the logged-in user's credentials (and therefore with user's permissions). This requires the storage endpoint to be configured for user validation against the internal Keycloak instance, since the access tokens are generated by Keycloak.

If your storage endpoint is not configured to validate users through Keycloak, presigned URL generation will fail. To resolve this, you can modify the deployment behavior by updating your `config.yaml` file to override the default behavior and use system credentials instead of user credentials for presigned URL generation.

> [!IMPORTANT]
> When using system credentials fallback, users can generate presigned URLs with elevated permissions beyond their normal access level. For instance, if users typically have read-only access to buckets, they could generate presigned URLs with DELETE permissions and use those URLs to delete files.

To enable system credentials fallback for presigned URLs generation, add the following to your `config.yaml`:

```yaml
edp:
  presignedUrlCredentialsSystemFallback: 'true'
```

### Testing S3 Compatible

Run a simple S3 mock server. Port 9191 will be used to expose a https server with self-signed certificate.

```bash
docker run --rm -p 9191:9191 -e initialBuckets=default,secondary -t adobe/s3mock
```

The following placeholder `<your-IP-address>` should be replaced with the external IP address of the host machine where the Docker container is being executed.

Configure EDP for the S3 compatible storage by either exporting environment variables or setting values in your `config.yaml`. If using an environment that requires proxy usage, ensure that you add `<your-IP-address>` to the `noProxy` variable in `config.yaml`.

Example `config.yaml` snippet to configure S3 compatible storage:

```yaml
edp:
  enabled: true
  storageType: "s3compatible"

  s3compatible:
    region: "us-east-1"
    accessKeyId: "testtesttest"
    secretAccessKey: "testtesttest"
    internalUrl: "https://<your-IP-address>:9191"
    externalUrl: "https://<your-IP-address>:9191"
    bucketNameRegexFilter: ".*"
    edpExternalCertVerify: false
    edpInternalCertVerify: false
```

Since this mock endpoint does not support event notifications, make sure scheduled synchronization is enabled as described in the [synchronization section](#storage-synchronization).

Deploy the application via Ansible using your configuration. After successful deployment, upload files using either WebGUI or cURL:

```bash
curl -X PUT "https://localhost:9191/default/test.txt" --upload-file test.txt -H "Content-Type: application/octet-stream" -k
```

## Development

To support changes in the database, a migration strategy software [Alembic](https://alembic.sqlalchemy.org/en/latest/) was introduced. This enabled upgrading the database schema based on model changes. It is done automatically each time the container starts and it ensures that the database schema is migrated to the newest version. If any changes are introduced into database models in [app/models.py](app/models.py) new migrations need to be generated. An instruction on how to generate such migrations is available in a separate [README.md](app/alembic/README.md).
