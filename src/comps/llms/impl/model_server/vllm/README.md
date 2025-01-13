# vLLM LLM Model Server

This document focuses on using the [Virtual Large Language Model (vLLM)](https://github.com/vllm-project/vllm) as a LLM.

vLLM is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## Getting Started

### 0. Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the dotenv configuration files.
```bash
export HF_TOKEN=${your_hf_api_token}
```

### 🚀 Start the vLLM Service via script (Option 1)
1.1. Run the script

```bash
# for hpu device (default)
export LLM_DEVICE='hpu'

# for cpu device
export LLM_DEVICE='cpu'

chmod +x run_vllm.sh
./run_vllm.sh
```
The script initiates a Docker container with the vLLM model server running on port `LLM_VLLM_PORT` (default: **8008**). Configuration settings are specified in the environment configuration files [docker/.env.hpu](docker/.env.hpu) and [docker/.env.cpu](docker/.env.cpu) files. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

#### 1.2. Verify the vLLM Service
Below examples are presented for hpu device. 

First, check the logs to confirm the service is operational:
```bash
docker logs -f llm-vllm-model-server
```

The following log messages indicate that the startup of model server is completed:
```bash
INFO 09-05 12:17:56 habana_model_runner.py:940] [Warmup][Decode][1023/1024] batch_size:2 seq_len:16 free_mem:5.414 GiB
INFO 09-05 12:17:56 habana_model_runner.py:940] [Warmup][Decode][1024/1024] batch_size:1 seq_len:16 free_mem:5.414 GiB
INFO 09-05 12:17:56 habana_model_runner.py:1007] Warmup finished in 1689 secs, allocated 2.499 GiB of device memory
INFO 09-05 12:17:56 habana_executor.py:83] init_cache_engine took 73.7 GiB of device memory (89.21 GiB/94.62 GiB used) and -4.57 GiB of host memory (107.5 GiB/1007 GiB used)
WARNING 09-05 12:17:56 serving_chat.py:391] No chat template provided. Chat API will not work.
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:80 (Press CTRL+C to quit)
```

Send the request to model server:

```bash
curl http://localhost:8008/v1/completions \
    -X POST \
    -d '{"model": "mistralai/Mistral-7B-Instruct-v0.1", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
    -H "Content-Type: application/json"
```

Expected output:
```json
{
  "id": "cmpl-1d9266525da24c5ba747e69208f71332",
  "object": "text_completion",
  "created": 1725543426,
  "model": "mistralai/Mistral-7B-Instruct-v0.1",
  "choices": [
    {
      "index": 0,
      "text": "\n\nDeep Learning is a subset of Machine Learning that is concerned with algorithms inspired by the structure and function of the brain. It is a part of Artificial",
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": {
    "prompt_tokens": 6,
    "total_tokens": 38,
    "completion_tokens": 32
  }
}
```
### 🚀 2. Deploy vLLM Service with LLM Microservice using Docker Compose (Option 2)

To launch vLLM Service along with the LLM Microservice, follow these steps:

#### 2.1. Modify the environment configuration file to align it to your case

For HPU device (Gaudi), modify the `./docker/.env.hpu` file:

```env
#HF_TOKEN=<your-hf-api-key>

## VLLM Model Server Settings ##
LLM_VLLM_MODEL_NAME="mistralai/Mistral-7B-Instruct-v0.1"
LLM_VLLM_PORT=8008

HABANA_VISIBLE_DEVICES=all
OMPI_MCA_btl_vader_single_copy_mechanism=none
PT_HPU_ENABLE_LAZY_COLLECTIVES=true
PT_HPU_LAZY_ACC_PAR_MODE=0
VLLM_CPU_KVCACHE_SPACE=40
VLLM_DTYPE=bfloat16
VLLM_MAX_NUM_SEQS=128
VLLM_SKIP_WARMUP=false
VLLM_TP_SIZE=1

[...]
```

#### 2.2. Start the Services using Docker Compose

To build and start the services using Docker Compose

```bash
cd docker

# for HPU device (Gaudi)
docker compose --env-file=.env.hpu -f docker-compose-hpu.yaml up --build -d
```

#### 2.3. Verify the Services

- Test the `llm-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8008/v1/completions \
        -X POST \
        -d '{"model": "mistralai/Mistral-7B-Instruct-v0.1", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
        -H "Content-Type: application/json"
    ```
    **NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

- Check the `llm-vllm-microservice` status:

    ```bash
    curl http://localhost:9000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-vllm-microservice` for **non-streaming mode** using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":false}' \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-vllm-microservice` for **streaming mode** using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":true}' \
        -H 'Content-Type: application/json'
    ```

#### 2.4. Service Cleanup

To cleanup the services using Docker Compose:

```bash
cd docker

# for HPU device (Gaudi)
docker compose -f docker-compose-hpu.yaml down
```
