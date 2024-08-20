# Mosec Embedding Server

This folder contains the implementation of the [Mosec](https://github.com/mosecorg/mosec) server for an embedding model.

## Getting Started

To get started with Mosec, follow these steps:

1. The pipeline was tested on `BAAI/bge-large-zh`. Modify `model/model-config.yaml` if you'd like to use another embedding model.
2. Run `run_mosec.sh` to build a docker container and start the server.
```bash
chmod +x run_mosec.sh
./run_mosec.sh
```

## Client test

```shell
curl -X POST http://127.0.0.1:8000/v1/embeddings -H "Content-Type: application/json" -d '{"inputs": "hello world"}'
```
