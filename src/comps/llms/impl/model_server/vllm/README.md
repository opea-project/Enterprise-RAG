# vLLM LLM Model Server


This README provides instructions on how to run a model server using [vLLM](https://github.com/vllm-project/vllm).

[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products). This guide provides an example on how to launch vLLM serving endpoint on CPU and Gaudi accelerators.

## Start vLLM Model Server
To get started with vLLM, follow these steps:

```bash
# for hpu device
chmod +x run_vllm_hpu.sh
./run_vllm_hpu.sh

# for cpu device
chmod +x run_vllm_cpu.sh
./run_vllm_cpu.sh
```
The script starts a Docker container running the vLLM model server, which defaults to exposing the service on port `LLM_VLLM_PORT` (default: **8008**). To change the port or the model (Intel/neural-chat-7b-v3-3), please edit the [docker/.env](docker/.env) or edit the Bash script accordingly.


**Verify if your vLLM model server is running:**  
Below examples are presented for hpu device. 

Check the logs to confirm the service is operational:
```bash
docker logs -f vllm-gaudi-model-server
```

The following log messages indicate that the startup of model server ic completed:
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

**Test your vLLM model server using the following command**:

```bash
curl http://localhost:8008/v1/completions \
    -X POST \
    -d '{"model": "Intel/neural-chat-7b-v3-3", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
    -H "Content-Type: application/json"
```

Expected output:
```json
{
  "id": "cmpl-1d9266525da24c5ba747e69208f71332",
  "object": "text_completion",
  "created": 1725543426,
  "model": "Intel/neural-chat-7b-v3-3",
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

## 🚀 Set up vLLM model server along with the OPEA LLM Microservice with Docker Compose

To launch vLLM along with the OPEA LLM Microservice, follow these steps:

1. **Configure the `./docker/.env` file**:

    "Ensure the `./docker/.env` file in the root directory aligns with your requirements:

    ```env
    HF_TOKEN=<your-hf-api-key>

    HABANA_VISIBLE_DEVICES=all
    LLM_VLLM_MODEL_NAME="Intel/neural-chat-7b-v3-3"
    LLM_VLLM_PORT=8008
    [...]
    ```

2. **Start the Services using Docker Compose**:

    Build and start the services using Docker Compose:

    ```bash
    cd docker
    docker compose -f docker-compose-hpu.yaml up --build -d
    ```


3. **Test the Services**:

    Test the `llm-vllm-model-server` using the following command:
    ```bash
    curl http://localhost:8008/v1/completions \
        -X POST \
        -d '{"model": "Intel/neural-chat-7b-v3-3", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}' \
        -H "Content-Type: application/json"
    ```
    **NOTICE**: First ensure that the model server is operational. Warming up might take a while, and during this phase, the endpoint won't be ready to serve the query.

    Check the `llm-vllm-microservice` status:

    ```bash
    curl http://localhost:9000/v1/health_check\
        -X GET \
        -H 'Content-Type: application/json'
    ```

    Test the `llm-vllm-microservice` for non-streaming mode using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":false}' \
        -H 'Content-Type: application/json'
    ```

    Test the `llm-vllm-microservice` for non-streaming mode using the following command:
    ```bash
    curl http://localhost:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":true}' \
        -H 'Content-Type: application/json'
    ```

4. **Cleanup the Services using Docker Compose**:

    To cleanup the services using Docker Compose:

    ```bash
    cd docker
    docker-compose -f docker-compose-hpu.yaml down
    ```
