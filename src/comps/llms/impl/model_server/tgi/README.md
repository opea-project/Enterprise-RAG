# TGI LLM Model Server

This document focuses on using the [Text Generation Inference (TGI)](https://github.com/huggingface/text-generation-inference) as a LLM.


## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the [.env](docker/.env) file.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 1. Start the TGI Service via script (Option 1)
1.1. Run the script

```bash
# for HPU device (Gaudi)
export LLM_DEVICE='hpu'

# for CPU device
export LLM_DEVICE='cpu'

chmod +x run_tgi.sh
./run_tgi.sh
```
The script initiates a Docker container with the TGI model server running on port `LLM_TGI_PORT` (default: **8008**). Configuration settings are specified in the environment configuration files [docker/.env.hpu](docker/.env.hpu) and [docker/.env.cpu](docker/.env.cpu) files. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

#### 1.2. Verify the TGI Service

```bash
curl http://localhost:8008/generate -X POST -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' -H 'Content-Type: application/json'
```

Expected output:
```json
{"generated_text":"\n\nDeep learning is part of a broader family of machine learning methods referred to as"}
```

### 🚀 2. Deploy TGI Service with OPEA LLM Microservice using Docker Compose (Option 2)
To launch TGI Service along with the OPEA LLM Microservice, follow these steps:

#### 2.1. Modify the environment configuration file to align it to your case

For HPU device (Gaudi), modify the `./docker/.env.hpu` file:
```env
# HF_TOKEN=<your-hf-api-key>

## TGI Model Server Settings ##
LLM_TGI_MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.1"
LLM_TGI_PORT=8008
[...]

## HABANA Settings ##
HABANA_VISIBLE_DEVICES=all
SHARDED=true
[...]
```

For CPU device, modify the `./docker/.env.cpu` file:
```env
# HF_TOKEN=<your-hf-api-key>

## TGI Model Server Settings ##
LLM_TGI_MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.1"
LLM_TGI_PORT=8008
[...]
```


#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose

```bash
cd docker

# for HPU device (Gaudi)
docker compose --env-file=.env.hpu -f  docker-compose-hpu.yaml up --build -d

# for CPU device
docker compose --env-file=.env.cpu -f  docker-compose-cpu.yaml up --build -d

```


#### 2.3. Verify the Services

 - Test the `llm-tgi-model-server` using the following command:

    ```bash
    curl localhost:8008/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
        -H 'Content-Type: application/json'
    ```

- Check the `llm-tgi-microservice` status:
    ```bash
    curl http://localhost:9000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-tgi-microservice` for **non-streaming mode** using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-tgi-microservice` for **streaming mode** using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
        -H 'Content-Type: application/json'
    ```

#### 2.4. Service Cleanup

To cleanup the services, run the following commands:

```bash
cd docker

# for HPU device (Gaudi)
docker compose -f docker-compose-hpu.yaml down

# for CPU device
docker compose -f docker-compose-cpu.yaml down
```

