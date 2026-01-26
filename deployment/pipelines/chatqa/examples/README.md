| Pipeline                                      | Platform | Description                                                                                       |
|----------------------------------------------|----------|---------------------------------------------------------------------------------------------------|
| `hpu-tei.yaml`                               | Gaudi    | Basic ChatQnA pipeline for Gaudi that uses Text Embeddings Inference from Huggingface for embeddings. |
| `hpu_torch.yaml`                             | Gaudi    | Basic chatQnA pipeline for Gaudi using TorchServe for embeddings.                                     |
| `hpu-torch-inguard.yaml`                     | Gaudi    | A pipeline for ChatQnA with Gaudi backend that uses TorchServe for embeddings and includes LLMGuard for input scanning. |
| `hpu-torch-inguard-outguard.yaml`            | Gaudi    | Similar to the Gaudi Torch pipeline but includes both input and output LLMGuard components. Uses TorchServe for embeddings. |
| `cpu-tei-inguard-outguard.yaml`              | Xeon     | A Xeon pipeline for chatQnA that includes LLMGuard for input and output scanning. Uses Text Embeddings Inference for embeddings. |
| `cpu-torch.yaml`                             | Xeon    | Basic ChatQnA pipeline for Xeon using TorchServe for embeddings.           |
| `cpu-embedding-vllm.yaml`                    | Xeon     | Basic ChatQnA pipeline for Xeon using vLLM for embeddings. |
| `cpu-torch-inguard-outguard.yaml`            | Xeon     | Similar to the Xeon Torch pipeline but includes LLMGuard for both input and output scanning. Uses TorchServe for embeddings. |
