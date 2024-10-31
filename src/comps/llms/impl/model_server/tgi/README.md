# TGI LLM Model Server

This document focuses on using the [Text Generation Inference (TGI)](https://github.com/huggingface/text-generation-inference) as a LLM.


## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the dotenv configuration files.

```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 1. Start the TGI Service via script (Option 1)
#### 1.1. Run the script

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

### 🚀 2. Deploy TGI Service with LLM Microservice using Docker Compose (Option 2)
To launch TGI Service along with the LLM Microservice, follow these steps:

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

### 3. Run FP8 Quantization with TGI on HPU device
In order to run a fp8 quantized model, you need do the following:

1. Modify `docker/.env.hpu` file - add `HF_TOKEN` and modify HABANA related envs to suit your needs. Add following parameters to ensure best performance during quantization and for later TGI serving ([source](https://github.com/huggingface/tgi-gaudi?tab=readme-ov-file#running-tgi-with-fp8-precision)).

```bash
## Provide your Hugging Face API key to enable access to Hugging Face models.
HF_TOKEN=<your hf token>
HUGGINGFACE_HUB_CACHE=../docker/data

MAX_INPUT_TOKENS=1024
MAX_TOTAL_TOKENS=2048
BATCH_SIZE=1
PREFILL_BATCH_BUCKET_SIZE=2
BATCH_BUCKET_SIZE=32
PAD_SEQUENCE_TO_MULTIPLE_OF=256
MAX_BATCH_PREFILL_TOKENS=2048
MAX_BATCH_TOTAL_TOKENS=65536
MAX_WAITING_TOKENS=7
WAITING_SERVED_RATIO=1.2
MAX_CONCURRENT_REQUESTS=64

IF_FP8_QUANTIZATION=true
FP8_QUANTIZE_MODEL_PATH=<path hqt_output folder>
```

2. Run the provided docker container to quantize the model. If you already have a fp8 quantize model, skip quantization and provide a path to `hqt_output` folder in `FP8_QUANTIZE_MODEL_PATH` env.

Refer to [optimum-habana](https://github.com/huggingface/optimum-habana/tree/main/examples/text-generation) for more information on fp8 quantization.

 ```bash
cd fp8_quantization
docker compose --env-file ../docker/.env.hpu -f docker-compose.yaml up -d --build
docker attach llm-fp8-quantization
```

Manually attaching to the container is required due to an issue with tqdm not logging the progress with docker compose up([source](https://github.com/tqdm/tqdm/issues/771)). If you don't need to use the progress of the quantization, you can skip this step.

In order to stop and remove the container, use following command:

```bash
docker compose -f docker-compose.yaml down
```

3. Provide a path to `hqt_output` folder with quantized configuration in `FP8_QUANTIZE_MODEL_PATH` env and set `IF_FP8_QUANTIZATION=true` - you can do this by either modyfing a `docker/.env.hpu` file or exporting variables manually. Next, run the TGI, either with a bash script or with a docker compose.

```bash
# with docker compose
cd ../docker && docker compose --env-file=.env.hpu -f docker-compose-hpu-fp8.yaml up --build llm-tgi-fp8-model-server

# with the bash script
cd .. && LLM_DEVICE=hpu ./run_tgi.sh
```

In order to stop and remove the TGI container, use following command:

```bash
docker compose -f docker-compose-hpu-fp8.yaml down
```