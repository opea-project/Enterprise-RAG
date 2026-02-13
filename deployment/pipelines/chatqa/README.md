| Pipeline                                      | Platform | Description                                                                                       |
|----------------------------------------------|----------|---------------------------------------------------------------------------------------------------|
| `examples/hpu-tei.yaml`                      | Gaudi    | Basic ChatQnA pipeline for Gaudi that uses Text Embeddings Inference from Huggingface for embeddings. |
| `examples/hpu-torchserve.yaml`                    | Gaudi    | Basic chatQnA pipeline for Gaudi using TorchServe for embeddings.                                     |
| `reference-hpu.yaml`                         | Gaudi    | A pipeline for ChatQnA with Gaudi backend that uses TorchServe for embeddings and includes LLMGuard for input scanning. |
| `examples/hpu-torchserve-inguard-outguard.yaml`   | Gaudi    | Similar to the examples/hpu-torchserve.yaml pipeline but includes both input and output LLMGuard components. Uses TorchServe for embeddings. |
| `examples/cpu-tei.yaml`                      | Xeon     | Basic ChatQnA Xeon pipeline for chatQnA that uses Text Embeddings Inference for embeddings. |
| `examples/cpu-torchserve.yaml`                    | Xeon     | Basic ChatQnA pipeline for Xeon using TorchServe for embeddings.           |
| `examples/cpu-embedding-vllm.yaml`           | Xeon     | Basic ChatQnA pipeline for Xeon that uses vLLM for embeddings with OpenAI-compatible API. |
| `reference-cpu.yaml`                         | Xeon     | A pipeline for ChatQnA with Xeon backend that uses TorchServe for embeddings and includes LLMGuard for input scanning. |
| `examples/hpu-torchserve-inguard-outguard.yaml`   | Xeon     | Similar to the examples/cpu-torchserve.yaml pipeline but includes LLMGuard for both input and output scanning. Uses TorchServe for embeddings. |
| `reference-external-endpoint.yaml`   | Xeon     | Similar to the reference-cpu.yaml pipeline but it uses external endpoint for inference instead of deploying vLLM |
