| Pipeline                                      | Platform | Description                                                                                       |
|----------------------------------------------|----------|---------------------------------------------------------------------------------------------------|
| `hpu-tei.yaml`                               | Gaudi    | Basic ChatQnA pipeline for Gaudi that uses Text Embeddings Inference from Huggingface for embeddings. |
| `hpu-torchserve.yaml`                             | Gaudi    | Basic chatQnA pipeline for Gaudi using TorchServe for embeddings.                                     |
| `hpu-torchserve-inguard.yaml`                     | Gaudi    | A pipeline for ChatQnA with Gaudi backend that uses TorchServe for embeddings and includes LLMGuard for input scanning. |
| `hpu-torchserve-inguard-outguard.yaml`            | Gaudi    | Similar to the Gaudi Torch pipeline but includes both input and output LLMGuard components. Uses TorchServe for embeddings. |
| `cpu-tei-inguard-outguard.yaml`              | Xeon     | A Xeon pipeline for chatQnA that includes LLMGuard for input and output scanning. Uses Text Embeddings Inference for embeddings. |
| `cpu-torchserve.yaml`                             | Xeon    | Basic ChatQnA pipeline for Xeon using TorchServe for embeddings           |
| `cpu-torchserve-inguard-outguard.yaml`            | Xeon     | Similar to the Xeon Torch pipeline but includes LLMGuard for both input and output scanning. Uses TorchServe for embeddings. |
