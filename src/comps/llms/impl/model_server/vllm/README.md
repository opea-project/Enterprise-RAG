# vLLM LLM Model Server

This document focuses on using the [vLLM](https://github.com/vllm-project/vllm) as a LLM.

vLLM is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## Table of Contents

1. [vLLM LLM Model Server](#vllm-llm-model-server)
2. [Getting Started](#getting-started)
   - 2.1. [Prerequisite](#prerequisite)
   - 2.2. [🚀 Start the vLLM Service via script (Option 1)](#-start-the-vllm-service-via-script-option-1)
     - 2.2.1. [Run the script](#run-the-script)
     - 2.2.2. [Verify the vLLM Service](#verify-the-vllm-service)
   - 2.3. [🚀 Deploy vLLM Service with LLM Microservice using Docker Compose (Option 2)](#-deploy-vllm-service-with-llm-microservice-using-docker-compose-option-2)
     - 2.3.1. [Modify the environment configuration file to align it to your case](#modify-the-environment-configuration-file-to-align-it-to-your-case)
     - 2.3.2. [Start the Services using Docker Compose](#start-the-services-using-docker-compose)
     - 2.3.3. [Service Cleanup](#service-cleanup)
   - 2.4. [Verify the Services](#verify-the-services)
   - 2.5. [Run FP8 Quantization with vLLM on HPU device](#run-fp8-quantization-with-vllm-on-hpu-device)
     - 2.5.1. [Perform model quantization](#perform-model-quantization)
     - 2.5.2. [Run vLLM with quantized model](#run-vllm-with-quantized-model)
   - 2.6. [vLLM for Xeon based on Red Hat® Universal Base Image](#vllm-for-xeon-based-on-red-hat-universal-base-image)

## Getting Started

### Prerequisite
Provide your Hugging Face API key to enable access to Hugging Face models. Alternatively, you can set this in the dotenv configuration files.
```bash
export HF_TOKEN=${your_hf_api_token}
```

Also, create a folder to preserve model data on host and change the ownership to the id that would match user in the image:
```bash
mkdir -p docker/data/
sudo chown -R 1000:1000 ./docker/data
```

### 🚀 Start the vLLM Service via script (Option 1)
#### Run the script

```bash
# for hpu device (default)
export LLM_DEVICE='hpu'

# for cpu device
export LLM_DEVICE='cpu'

chmod +x run_vllm.sh
./run_vllm.sh
```
The script initiates a Docker container with the vLLM model server running on port `LLM_VLLM_PORT` (default: **8008**). Configuration settings are specified in the environment configuration files [docker/hpu/.env](docker/hpu/.env) and [docker/cpu/.env](docker/cpu/.env) files. You can adjust these settings by modifying the appropriate dotenv file or by exporting environment variables.

#### Verify the vLLM Service
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

### 🚀 Deploy vLLM Service with LLM Microservice using Docker Compose (Option 2)

To launch vLLM Service along with the LLM Microservice, follow these steps:

#### Modify the environment configuration file to align it to your case

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

#### Start the Services using Docker Compose

To build and start the services using Docker Compose

```bash
# for CPU device
cd docker/cpu
mkdir -p data
export UID && docker compose --env-file=.env -f docker-compose.yaml up --build -d

# for HPU device (Gaudi)
cd docker/hpu
mkdir -p data
docker compose --env-file=.env -f docker-compose.yaml up --build -d
```

Note: Due to secure container best practices, main process is started as non-privileged user.
Due to the fact it uses volume mounts, the volume directory `data/` must be created beforehand.

#### Service Cleanup

To cleanup the services using Docker Compose:

```bash
cd docker

# for HPU device (Gaudi)
docker compose -f docker-compose-hpu.yaml down
```

### Verify the Services

- Test the `llm-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8008/v1/completions \
        -X POST \
        -d '{"model": "Intel/neural-chat-7b-v3-3", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
        -H "Content-Type: application/json"
    ```
    **NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

- Check the `llm-vllm-microservice` status:

    ```bash
    curl http://localhost:9000/v1/health_check \
        -X GET \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-vllm-microservice` for **non-streaming mode** using the following command:
    ```bash
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
                "max_new_tokens":17,
                "top_p":0.95,
                "temperature":0.01,
                "stream":false
            }' \
        -H 'Content-Type: application/json'
    ```

- Test the `llm-vllm-microservice` for **streaming mode** using the following command:
    ```bash
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

### Run FP8 Quantization with vLLM on HPU device

In order to work with a fp8 quantized model, you need to do the following:
* Perform model quantization with provided utility. Only needed if model isn't quantized.
* Run vLLM with FP8 quantized model.

> [!NOTE]
> It's a known issue that `mistralai/Mixtral-8x7B-Instruct-v0.1` does not run after quantization with standard parameters.
>
> Currently the FP8 quantization was verified for model `Intel/neural-chat-7b-v3-3`. Other models need verification and may require some work to be fully supported.


#### Perform model quantization

1. Download dataset for calibration of model in `pkl` file format, e.g. open-orca dataset.
1. Modify `docker/.env.hpu` file - add `HF_TOKEN` and modify HABANA related envs to suit your needs.

   Minimal list of updated settings includes these:
    ```ini
    ## Provide your Hugging Face API key to enable access to Hugging Face models.
    HF_TOKEN=<your-hf-api-key>

    ## VLLM Model Server Settings ##
    LLM_VLLM_MODEL_NAME="Intel/neural-chat-7b-v3-3"

    ## FP8 Quantization settings
    FP8_DATASET_PATH=<path to calibration dataset in pkl format>
    ```

1. Define variable pointing to host directory containing models downloaded from Hugging Face:
    ```bash
    export HUGGINGFACE_HUB_CACHE=<path to HF cache directory>
    ```
1. Run the provided docker container to quantize the model.

    ```bash
    cd model_server/vllm/fp8_vllm
    docker compose -f docker-compose.yaml --env-file ../docker/hpu/.env up --build
    ```

   After the quantization command concludes the hots model data directory will include subdirectory with quantization outcome, e.g.:
   `${HUGGINGFACE_HUB_CACHE}/inc/<name_of_the_model>`.

#### Run vLLM with quantized model

1. Modify `docker/.env.hpu` file - add `HF_TOKEN` and modify HABANA related envs to suit your needs.
2. Ensure model and measurements will be reachable for vLLM under Hugging Face model directory, e.g.: `${HUGGINGFACE_HUB_CACHE}/inc/<name_of_the_model>` or override the variable `QUANT_CONFIG`.
3. Run vLLM model server in FP8-enabled mode.
   ```bash
   cd model_server/vllm
   IF_FP8_QUANTIZATION=true ./run_vllm.sh
   ```

### vLLM for Xeon based on Red Hat® Universal Base Image
This image is based on Universal Base Image 9 (UBI) maintained by Red Hat®. The image leverages `AMX` and `AVX-512` instruction extensions for improved inference. It runs vLLM in an unprivileged mode installed on top of UBI9 which makes it a perfect choice for OpenShift deployments on Xeon® as it works out-of-the-box. The image is publicly available on OPEA Docker Hub. It is compatible with all Xeon® CPUs since generation 4, codenamed *Sapphire Rapids*. The image is a different version of the vLLM image for CPU build and published by the vLLM project, so for deeper insights you can take a look at the [official documentation](https://docs.vllm.ai/en/stable/getting_started/installation/cpu).

If you want, you can use it as a standalone vLLM in your project.

- Leverages `AMX` and `AVX-512` for optimized inference
- Compatible with *Sapphire Rapids* and newer generation of Intel® Xeon® CPUs
- By default, `VLLM_CPU_KVCACHE_SPACE` is set to `40GiB`, however you can change it using an environment variable during runtime
- Docker Hub -> [docker.io/opea/vllm-cpu-ubi](https://hub.docker.com/r/opea/vllm-cpu-ubi)
- [Dockerfile](./docker/cpu_ubi/Dockerfile)


#### Building the Docker image
You can customize and build the image yourself if needed.
- Default build with Xeon optimizations enabled. Just run the `docker build` with default values.
```bash
docker build -f Dockerfile -t vllm-cpu-ubi:latest .
```
-  For machines without `avx512f`, `avx512_bf16`, `avx512_vnni` or `amx`, disable build optimizations using `--build-arg`.
```bash
docker build -f docker/Dockerfile.xeon-ubi\
        --build-arg VLLM_CPU_AVX512BF16=false \
        --build-arg VLLM_CPU_AVX512VNNI=false \
        --build-arg VLLM_CPU_DISABLE_AVX512=true \
        --build-arg VLLM_CPU_AMXBF16=false
        --tag vllm-xeon-ubi
```
- More details in [Build image from source](https://docs.vllm.ai/en/stable/getting_started/installation/cpu.html#build-image-from-source)

#### Running the Docker container as a standalone server
- Specify `VLLM_CPU_KVCACHE_SPACE`; it must be lower than your system memory (default is 40GB). A larger KV Cache can support more concurrent requests and longer context lengths.
```bash
docker run -d \
  -p 8000:8000 \
  -e VLLM_CPU_KVCACHE_SPACE=20 \
  -e HF_TOKEN=<YOUR_HF_TOKEN> \
  docker.io/opea/vllm-cpu-ubi:v0.12.0-ubi9 \
    --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype bfloat16
```
