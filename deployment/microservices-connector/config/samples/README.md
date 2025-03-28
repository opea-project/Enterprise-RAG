| Pipeline                                      | Platform | Description                                                                                       |
|----------------------------------------------|----------|---------------------------------------------------------------------------------------------------|
| `chatQnA_gaudi.yaml`                         | Gaudi    | Basic ChatQnA pipeline for Gaudi that uses Text Embeddings Inference from Huggingface for embeddings. |
| `chatQnA_gaudi_torch.yaml`                   | Gaudi    | Basic chatQnA pipeline for Gaudi using TorchServe for embeddings.                                     |
| `chatQnA_gaudi_torch_guard.yaml`             | Gaudi    | A pipeline for ChatQnA with Gaudi backend that uses TorchServe for embeddings and includes LLMGuard for input scanning. |
| `chatQnA_gaudi_torch_in_out_guards.yaml`     | Gaudi    | Similar to the Gaudi Torch pipeline but includes both input and output LLMGuard components. Uses TorchServe for embeddings. |
| `chatQnA_xeon_llm_guard.yaml`                | Xeon     | A Xeon pipeline for chatQnA that includes LLMGuard for input and output scanning. Uses Text Embeddings Inference for embeddings. |
| `chatQnA_xeon_torch.yaml`                    | Xeon     | Basic ChatQnA pipeline for Xeon using TorchServe for embeddings.           |
| `chatQnA_xeon_torch_llm_guard.yaml`          | Xeon     | Similar to the Xeon Torch pipeline but includes LLMGuard for both input and output scanning. Uses TorchServe for embeddings. |
