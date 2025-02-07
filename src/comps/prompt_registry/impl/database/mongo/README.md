# MongoDB database

This document focuses on using the [MongoDB](https://mongodb.com/) for Prompt Registry Microservice.

## Getting Started

### Prerequisites

You can set all required environmental variables in the [.env](../../microservice/.env) file.

### Start the MongoDB Service

To build and start the services use the docker-compose.yaml file provided:

```bash
docker compose --env-file ../../microservice/.env -f docker-compose.yaml up --build -d
```

### Verify the Services

In order to verify if services are working, use example requests provided in [README.md](../../../README.md)

### Service Cleanup

To cleanup the services, run the following command:

```bash
docker compose -f docker-compose.yaml down
```