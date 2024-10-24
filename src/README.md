# Intel(R) AI for Enterprise RAG Microservices Source Code

Following folder contains source code and tests for all microservices that are used in Enteprise RAG Application. It also contains source code for UI part of the application.

For information on a particular microservice, please go `comps/` folder, where all of the microservice are.

# Table of Contents

- [Prerequisites](#prerequisites)
- [Folder Structure](#folder-structure)

## Prerequisites
- Python 3.11 (recommended)
- Docker
- tox - required for tests

## Folder Structure
### Microservices

Microservice's implementation is available in `comps/` folder. Each microservice contains 3 important parts:

- `opea_<name of the microservice>_microservice.py` - a file containing microservice registration and initial parameters configuration
- `utils/` folder - containing implementation of all connector classes and wrappers for third-party libraries e.g. model servers
- `impl/` folder - containing all implementation details for third-party libraries implementation, e.g. configuration files and Dockerfiles, as well as configuration files for the microservice

### Test

For information on tests, please refer to [tests/README.md](tests/README.md).