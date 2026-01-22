# LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a LLM text generation service (TGI, vLLM or Ray) already running. Users need to set the LLM service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the LLM service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI/vLLM service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.

## Table of Contents

1. [LLM Microservice](#llm-microservice)
2. [Support Matrix](#support-matrix)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [Prerequisite: Start LLM Model Server](#prerequisite-start-llm-model-server)
   - 4.2. [🚀 Start LLM Microservice with Python (Option 1)](#-start-llm-microservice-with-python-option-1)
     - 4.2.1. [Install Requirements](#install-requirements)
     - 4.2.2. [Start Microservice](#start-microservice)
   - 4.3. [🚀 Start LLM Microservice with Docker (Option 2)](#-start-llm-microservice-with-docker-option-2)
     - 4.3.1. [Build the Docker Image](#build-the-docker-image)
     - 4.3.2. [Run the Docker Container](#run-the-docker-container)
   - 4.4. [Verify the LLM Microservice](#verify-the-llm-microservice)
     - 4.4.1. [Check Status](#check-status)
     - 4.4.2. [Sending a Request](#sending-a-request)
       - 4.4.2.1. [Example Input](#example-input)
       - 4.4.2.2. [Example Output](#example-output)
       - 4.4.2.3. [Example Output with additional Data](#example-output-with-additional-data)
5. [Validated Model](#validated-model)
6. [Additional Information](#additional-information)
   - 6.1. [Project Structure](#project-structure)
   - 6.2. [Tests](#tests)

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server name                 |  Status   |
| ----------------------------------| --------- |
| [VLLM](./impl/model_server/vllm/) | &#x2713;  |
| TGI                               | &#x2717;  |


## Configuration Options

The configuration for the LLM Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `LLM_USVC_PORT`                 | The port of the microservice, by default 9000.                                                                        |
| `LLM_MODEL_NAME`                | The name of language model to be used (e.g., "mistralai/Mistral-7B-Instruct-v0.1")                                             |
| `LLM_MODEL_SERVER`              | Specifies the type of model server (e.g. "vllm")                                                               |
| `LLM_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint, e.g., "http://localhost:8008"                                                       |
| `LLM_DISABLE_STREAMING`         | Disables streaming even if streaming has been enabled via the input query/request.                                    |
| `LLM_OUTPUT_GUARD_EXISTS`       | Informs LLM service if there is LLM output guard service after LLM, so the streaming is taken by LLM output guard.    |
| `LLM_TLS_SKIP_VERIFY`           | Skips tls certificate verification for inference endpoint |

Set below environment variables only for VLLM if remote model server is enabled with token based authentication (OAuth).
| `LLM_VLLM_CLIENT_ID`                      | The id of the client in auth provider |
| `LLM_VLLM_CLIENT_SECRET`                 | The secret of the client in auth provider |
| `LLM_VLLM_TOKEN_URL`                     | The token URL to get the access token |

Alternatively, static API KEY can be provided. This will override OAuth settings.
| `LLM_VLLM_API_KEY` | static API key for vllm endpoint |

## Getting started

There're 2 ways to run this microservice:
  - [via Python](#-start-llm-microservice-with-python-option-1)
  - [via Docker](#-start-llm-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start LLM Model Server

The LLM Microservice interacts with a LLM model endpoint, which must be operational and accessible at the the URL specified by the `LLM_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service.

### 🚀 Start LLM Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python opea_llm_microservice.py
```

### 🚀 Start LLM Microservice with Docker (Option 2)

#### Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/llm:latest -f comps/llms/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container:
```bash
docker run -d --name="llm-microservice" \
  --net=host \
  --ipc=host \
  opea/llm:latest
```

If the model server is running at a different endpoint than the default, update the `LLM_MODEL_SERVER_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
docker run -d --name="llm-microservice" \
  -e LLM_MODEL_SERVER_ENDPOINT="http://localhost:8008" \
  -e LLM_MODEL_NAME="meta-llama/Meta-Llama-3-70B" \
  -e LLM_MODEL_SERVER="vllm" \
  --net=host \
  --ipc=host \
  opea/llm:latest
```

### Verify the LLM Microservice

#### Check Status

```bash
curl http://localhost:9000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`. See the example below for more of an understanding.

The `streaming` parameter controls the API response format:
 - `stream=false` returns a complete text string,
 - `stream=true` streams the text in real time.

> [!NOTE]
> Ensure that your model server is running at `LLM_MODEL_SERVER_ENDPOINT` and is ready to accept requests. Be aware that the server may take some time to become fully operational; otherwise, the microservice will return an Internal Server Error.

##### Example Input

```bash
# non-streaming mode
curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{
                "messages": [
                      {
                        "role": "system",
                        "content": "### You are a helpful, respectful, and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. Refer also to the conversation history if you think it is relevant to the current question. Ignore all information that you think is not relevant to the question. If you dont know the answer to a question, please dont share false information. ### Search results:  \n\n"
                      },
                      {
                        "role": "user",
                        "content": "### Question: What is Deep Learning? \n\n"
                      }
                    ],
                "max_new_tokens":32,
                "top_p":0.95,
                "temperature":0.01,
                "stream":false
            }' \
        -H 'Content-Type: application/json'
```

```bash
# streaming mode
curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{
                "messages": [
                      {
                        "role": "system",
                        "content": "### You are a helpful, respectful, and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. Refer also to the conversation history if you think it is relevant to the current question. Ignore all information that you think is not relevant to the question. If you dont know the answer to a question, please dont share false information. ### Search results:  \n\n"
                      },
                      {
                        "role": "user",
                        "content": "### Question: What is Deep Learning? \n\n"
                      }
                    ],
                "max_new_tokens":32,
                "top_p":0.95,
                "temperature":0.01,
                "stream":true
            }' \
        -H 'Content-Type: application/json'
```

##### Example Output

The following examples demonstrate the LLM microservice output in both non-streaming and streaming modes.

- In **non-streaming mode** (stream=false), the service returns a single JSON response:

```json
{
  "id":"9a1b09face84c316c9a6297052d8b791",
  "text":"System: I am a helpful, respectful, and honest assistant designed to help you",
  "prompt":"### Question: Who are you? \n\n",
  "stream":false,
  "output_guardrail_params":null
}
```
- In **streaming mode** (stream=true), the response is sent in chunks, providing real-time updates for each word or phrase as it is generated.

```
data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":"Deep"},"finish_reason":null}]}
data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":" learning"},"finish_reason":null}]}
data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":" is"},"finish_reason":null}]}
...
data: {"id":"chatcmpl-xyz789","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":""},"finish_reason":"stop"}]}
data: [DONE]
```

##### Example Output with additional Data

If additional data is passed in LLMParamsDoc.data attribute, additional data is appended to the response. For example:

- In **non-streaming mode** (stream=false), the service returns a single JSON response:

```json
{
  "id": "9a1b09face84c316c9a6297052d8b791",
  "text": "System: I am a helpful, respectful, and honest assistant designed to help you",
  "prompt": "### Question: Who are you? \n\n",
  "stream": false,
  "output_guardrail_params": null,
  "data": { "reranked_docs": [{ "url": "https://example.com", "citation_id": 1, "vector_distance": 0.23, "reranker_score": 0.83 }] }
}
```
- In **streaming mode** (stream=true), the response is sent in chunks, providing real-time updates for each word or phrase as it is generated.

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":"Deep"},"finish_reason":null}]}
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":" learning"},"finish_reason":null}]}
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":" is"},"finish_reason":null}]}
...
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"mistralai/Mistral-7B-Instruct-v0.1","choices":[{"index":0,"delta":{"content":""},"finish_reason":"stop"}]}
data: [DONE]
json: { "reranked_docs": [{ "url": "https://example.com", "citation_id": 1, "vector_distance": 0.23, "reranker_score": 0.83 }] }
```

## Validated Model

To find validated models running on Gaudi, refer to the following resources:

 - **For vLLM**, see the [Supported Configuration](https://github.com/HabanaAI/vllm-fork/releases#Supported-Configurations).


## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the LLM microservice, including model servers integration and Dockerfiles.

- `utils/`: This directory contains utility scripts and modules used by the LLM Microservice for model servers connections.

#### Tests
- `src/tests/unit/llms/`: Contains unit tests for the LLM Microservice components
