# LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a LLM text generation service (TGI, vLLM or Ray) already running. Users need to set the LLM service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the LLM service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI/vLLM/Ray service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server name                 |  Status   | 
| ----------------------------------| --------- | 
| [TGI](./impl/model_server/tgi/)   | &#x2713;  | 
| [VLLM](./impl/model_server/vllm/) | &#x2713;  |
| RAY                               | &#x2717;  |


## Configuration Options

The configuration for the LLM Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `LLM_USVC_PORT`                 | The port of the microservice, by default 9000.                                                                        |
| `LLM_MODEL_NAME`                | The name of language model to be used (e.g., "Intel/neural-chat-7b-v3-3")                                             |
| `LLM_CONNECTOR`                 | The framework used to connect to the model. Supported values: 'langchain', 'generic'. If not specified, the generic connection method will be used. |
| `LLM_MODEL_SERVER`              | Specifies the type of model server (e.g. "tgi", "vllm")                                                               |
| `LLM_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint, e.g., "http://localhost:8008"                                                       |


## Getting started

### Prerequisite: Start LLM Model Server

The LLM Microservice interacts with a LLM model endpoint, which must be operational and accessible at the the URL specified by the `LLM_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the approppriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. 

### 🚀1. Start LLM Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

#### 1.1. Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

#### 1.2. Start Microservice 

```bash
python opea_llm_microservice.py
```


### 🚀2. Start LLM Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/llm:latest -f comps/llms/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:
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
  -e LLM_CONNECTOR="langchain" \
  -e LLM_MODEL_SERVER="vllm" \
  --net=host \
  --ipc=host \
  opea/llm:latest
```

### 3. Verify the LLM Microservice

#### 3.1. Check Status

```bash
curl http://localhost:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`. See the example below for more of an understanding.

The `streaming` parameter controls the API response format:
 - `streaming=false` returns a complete text string,
 - `streaming=true` streams the text in real time.

> **NOTE:** Ensure that your model server is running at `LLM_MODEL_SERVER_ENDPOINT` and is ready to accept requests. Be aware that the server may take some time to become fully operational; otherwise, the microservice will return an Internal Server Error.

**Example Input**

```bash
# non-streaming mode
curl http://localhost:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'
```

```bash
# streaming mode
curl http://localhost:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

**Example Output**

The following examples demonstrate the LLM microservice output in both non-streaming and streaming modes.

 - In **non-streaming mode** (streaming=false), the service returns a single JSON response:

    ```json
    {
      "id":"fd49a0d75f7f54089572fa30510f8d3a",
      "text":"\n\nDeep learning is a subset of machine learning that uses algorithms to learn from data",
      "prompt":"What is Deep Learning?"
    }
    ```
- In **streaming mode** (streaming=true), the response is sent in chunks, providing real-time updates for each word or phrase as it is generated:
    ```
    data: '\n'
    data: 'Deep'
    data: ' learning'
    data: ' is'
    data: ' a'
    data: ' subset'
    data: ' of'
    data: ' machine'
    data: ' learning'
    data: ' that'
    data: ' uses'
    data: ' artificial'
    data: ' neural'
    data: ' networks'
    data: [DONE]
    ```

## Validated Model

To find validated models running on Gaudi, refer to the following resources:

 - **For TGI**, see the [Tested Models and Configurations](https://github.com/huggingface/tgi-gaudi/releases#tested-models-and-configurations).
 - **For vLLM**, see the [Supported Configuration](https://github.com/HabanaAI/vllm-fork/releases#Supported-Configurations).


## Additional Information
### Project Structure

The project is organized into several directories:
- `impl/`: This directory contains the implementation. It includes the microservice folder with the Dockerfile for the microservice, and the `model_server` directory, which provides setup and running instructions for various model servers, such as TGI or vLLM.
- `utils/`: This directory contains utility scripts and modules that are used by the LLM Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── .env
  │   │   ├── Dockerfile
  │   │   └── requirements.txt
  │   │
  │   ├── model_server/
  │   │   ├── tgi/
  │   │   │   ├── README.md
  │   │   │   └── docker/
  │   │   │       ├── .env
  │   │   │       ├── docker-compose-cpu.yml
  │   │   │       └── docker-compose-hpu.yml
  │   │   │  
  │   │   └── ...
  │   └── ...
  │
  ├── utils/
  │   ├── opea_llm.py
  │   └── connectors/
  │       ├── connector.py
  │       ├── generic.py
  │       └── wrappers/
  │           └── wrapper_langchain.py
  │
  ├── README.md
  └── opea_llm_microservice.py
```

#### Tests
- `src/tests/unit/llms/`: Contains unit tests for the LLM Microservice components



