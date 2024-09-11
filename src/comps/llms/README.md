DISCLAIMER: The solution is verified for streaming and non_streaming modes for TGI on CPU and HPU devices. WIP for VLLM


# OPEA LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a LLM text generation service (TGI, vLLM or Ray) already running. Users need to set the LLM service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the LLM service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI/vLLM/Ray service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.


## Example input

LLM microservice as an input accepts a json. An example request can look as follows:

```bash
curl http://localhost:9000/v1/chat/completions \
-X POST \
-d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03, "streaming":false}' \
-H 'Content-Type: application/json'
```

## Example output

The output of the LLM microservice is a json that contains the generated text, which is crafted based on the input query provided. The example below illustrates this in non-streaming mode (using streaming:false), as shown in the cURL request above.

```json
{
  "id":"fd49a0d75f7f54089572fa30510f8d3a",
  "text":"\n\nDeep learning is a subset of machine learning that uses algorithms to learn from data",
  "prompt":"What is Deep Learning?"
}
```

## Configuration Options

Configuration for the OPEA LLM Microservice is defined in the [config.ini](./config.ini) file, and can be adjusted there or via correspoding environment variables.

Examplary configuration:

```ini
# OPEA LLM Microservice Configuration File
[Logging]
# env - LOG_LEVEL
log_level=INFO
# env - LOG_PATH
log_path=/tmp/opea/microservices/llm/llm.log

[OPEA_Microservice]
# env - USVC_NAME
name=opea_service@llm
# env - USVC_HOST
host=0.0.0.0
# env - USVC_PORT
port=9000

[Model]
# env - LLM_NAME
model_name="Intel/neural-chat-7b-v3-3"
# env - FRAMEWORK
framework="langchain"
# env - MODEL_SERVER
model_server="tgi"
# env - LLM_MODEL_SERVER_ENDPOINT
model_server_endpoint="http://localhost:8080"

```

What each section and option does:

| **Configuration Option**  | **Defaults**                | **Environment Variable**    | **Description**                                                              |
|---------------------------|-----------------------------|-----------------------------|------------------------------------------------------------------------------|
| **[Logging]**             |                             |                             | This section contains options related to logging.                            |
| `log_level`               | Defined in `config.ini`     | `LOG_LEVEL`                 | The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).                   |
| `log_path`                | Defined in `config.ini`     | `LOG_PATH`                  | The path to the log file.                                                    |
| **[OPEA_Microservice]**   |                             |                             | This section contains options related to the microservice itself             |
| `name`                    | Defined in `config.ini`     | `USVC_NAME`                 | The name of the microservice.                                                |
| `host`                    | Defined in `config.ini`     | `USVC_HOST`                 | The host of the microservice.                                                |
| `port`                    | Defined in `config.ini`     | `USVC_PORT`                 | The port of the microservice.                                                |
| **[Model]**               |                             |                             | This section contains options related to the model server.                   |
| `model_name`              | Defined in `config.ini`     | `LLM_NAME`                  | The name of the language model                                               |
| `framework`               | Defined in `config.ini`     | `FRAMEWORK`                 | The framework used for the language model.                                   |
| `model_server`            | Defined in `config.ini`     | `MODEL_SERVER`              | The model server used for the language model.model.                          |
| `model_server_endpoint`   | Defined in `config.ini`     | `LLM_MODEL_SERVER_ENDPOINT` | The endpoint of the model server                                             |




# 🚀1. Start OPEA LLM Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

## 1.1 Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

## 1.2 Start LLM Model Servver

The OPEA LLM Microservice interacts with a llm model endpoint that must be operational and reachable at the URL specified by the `LLM_MODEL_SERVER_ENDPOINT` environment variable or the `model_server_endpoint` option in the `Model` section of the [config.ini](config.ini) file.

Depending on the model server you want to use for obtaining scores, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. 


### Start TGI Service

```bash
export HF_TOKEN=${your_hf_api_token}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/gen-ai-comps:llms"
docker run -p 8008:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${your_hf_llm_model}
```

### Start vLLM Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker run -it --name vllm_service -p 8008:80 -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -v ./data:/data vllm:cpu /bin/bash -c "cd / && export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --model ${your_hf_llm_model} --port 80"
```

### Start Ray Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export TRUST_REMOTE_CODE=True
docker run -it --runtime=habana --name ray_serve_service -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -p 8008:80 -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e TRUST_REMOTE_CODE=$TRUST_REMOTE_CODE ray_serve:habana /bin/bash -c "ray start --head && python api_server_openai.py --port_number 80 --model_id_or_path ${your_hf_llm_model} --chat_processor ${your_hf_chatprocessor}"
```

## 1.3 Verify the LLM Service

### Verify the TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

###  Verify the vLLM Service

```bash
curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

### Verify the Ray Service

```bash
curl http://${your_ip}:8008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "messages": [
        {"role": "assistant", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Deep Learning?"},
    ],
  "max_tokens": 32,
  "stream": True
  }'
```


### 1.4. Start Microservice 

  ```bash
  $ python opea_llm_microservice.py


  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
  [2024-08-11 15:45:51,113] [    INFO] - HTTP server setup successful
  ```

### 🚀2. Start OPEA LLM Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Use the docker build command to create the Docker image. First, navigate to the src directory in the project’s root folder, as this directory contains the necessary source code required for building the image.
```bash
cd ../../
docker build -t opea/llm:latest -f comps/llms/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:
Once the image is built, you can run it using the docker run command. Before running the image, ensure the Model Server is already running. Please, refer to the documentation in the [model_server directory](./model_server) for instructions on how to run the specific model.

For example, assuming the TGI Model is serving rankings at `http://localhost:8008`, you can run the OPEA LLM Microservice with the following command:

```bash
docker run -d --name="llm-tei-microservice" \
  -e LLM_MODEL_SERVER_ENDPOINT=http://localhost:8008 \
  --net=host \
  --ipc=host \
  opea/llm:latest
```

# 3. OPEA LLM Microservice API

## 3.1 Check Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Usage

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`.

The `streaming` parameter determines the format of the data returned by the API. It will return text string with `streaming=false`, return text streaming flow with `streaming=true`.

```bash
# non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'

# streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

## 4. Support Matrix for Model-Server

Support for specific ranking model servers with Dockerfiles or build instruction.

| Model server name                 |  Status   | 
| ----------------------------------| --------- | 
| [TGI](./impl/model_server/tgi/)   | &#x2713;  | 
| [VLLM](./impl/model_server/vllm/) | &#x2713;  |
| RAY                               | &#x2717;  |

## 5. Validated Model

| Model                     | TGI-Gaudi | vLLM-CPU | vLLM-Gaudi | Ray |
| ------------------------- | --------- | -------- | ---------- | --- |
| Intel/neural-chat-7b-v3-3 | ✓         | ✓        | ✓          | ✓   |
| Llama-2-7b-chat-hf        | ✓         | ✓        | ✓          | ✓   |
| Llama-2-70b-chat-hf       | ✓         | -        | ✓          | x   |
| Meta-Llama-3-8B-Instruct  | ✓         | ✓        | ✓          | ✓   |
| Meta-Llama-3-70B-Instruct | ✓         | -        | ✓          | x   |
| Phi-3                     | x         | Limit 4K | Limit 4K   | ✓   |
