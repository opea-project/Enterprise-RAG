# TorchServe Embedding Model Server

This folder contains the implementation of the Torchserve server for an embedding model.

## Overview

TorchServe is a lightweight, scalable, and easy-to-use model serving library for PyTorch models. It provides a RESTful API for serving trained models, allowing users to deploy and serve their models in production environments. Moreover, Torchserve supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

## Getting Started

To get started with TorchServe, follow these steps:

1. Install TorchServe by running
```bash
pip install torchserve torch-model-archiver
```
2. The pipeline was tested on `sentence-transformers/all-MiniLM-L6-v2`. Modify `model/model-config.yaml` if you'd like to use another embedding model.
3. Run `build_docker_ts.sh` to package all model artifacts into a single model archive file, build a docker container and start a torchserve server.
```bash
chmod +x build_docker_ts.sh
./build_docker_ts.sh
```

For detailed instructions and examples, please refer to the [TorchServe documentation](https://pytorch.org/serve/).

## Folder Structure

- `docker/`: Contains a Dockerfile and support files.
- `model/`: Contains a model handler for Torchserve and its support files.
