# Evaluation Methodology

<!-- TOC -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
  - [Environment](#environment)
  - [Launch Service of RAG System](#launch-service-of-rag-system)
  - [Launch Service of LLM-as-a-Judge](#launch-service-of-llm-as-a-judge)
  - [Launch Service of Embeddings](#launch-service-of-embeddings)
- [Metrics](#metrics)
- [MultiHop (English dataset)](#multihop-english-dataset)
  - [Evaluation](#evaluation)
  - [Usage Guide](#usage-guide)
- [Acknowledgements](#acknowledgements)


<!-- /TOC -->

## Introduction

Retrieval-Augmented Generation (RAG) has recently gained traction in natural language processing. Numerous studies and real-world applications are leveraging its ability to enhance generative models through external information retrieval.

For evaluating the accuracy of a RAG pipeline, we use latest published dataset and 10+ metrics which are popular and comprehensive:

 - Dataset
   - [MultiHop](https://arxiv.org/pdf/2401.15391) (English dataset)


 - Metrics (measure accuracy of both the context retrieval and response generation).
   - [BLEU](../metrics/bleu)
   - [ROUGE(L)](../metrics/rogue)
   - [RAGAS](../metrics/ragas)
   - [Hits@4, Hits@10, MAP@10, MRR@10](../metrics/retrieval)
   
   See dedicated section [Metrics](#metrics) for full details.


## Prerequisites

### Environment

It is recommended to use Python virtual environments to manage dependencies. You can set it up as follow:

```sh
# Install python3-venv if not already installed
sudo apt-get install python3-venv

# Create and activate a virtual environment
python3 -m venv eval-erag-venv
source eval-erag-venv/bin/activate

# Upgrade pip and install required packages
pip install --upgrade pip
pip install -r requirements.txt
```

Export the `PYTHONPATH` environment variable pointing to the `src` folder in this repository to ensure proper module resolution.

### Launch Service of RAG System

Please refer to this [guide](../../../../../../deployment/README.md) to launch the service of RAG system.

> [!WARNING]
> The RAG service must be accessible locally. Ensure no network restrictions or proxies block local access.

If your system uses a proxy, ensure the no_proxy environment variable includes the following to allow local access without proxying:

```sh
export no_proxy=localhost,127.0.0.1,erag.com,s3.erag.com
```

### Launch Service of LLM-as-a-Judge

_This step is required only for computing RAGAS metrics._

To calculate RAGAS metrics, a separate LLM as a Judge service, a dedicated language model responsible for evaluating answer quality, is required. You can launch the service by using existing scripts provided elsewhere in the project.

To run VLLM model server, navigate to [src/comps/llms/impl/model_server/vllm](../../../../../../src/comps/llms/impl/model_server/vllm) and run the `run_vllm.sh` script:

```bash
# (Required) Hugging Face token
export HF_TOKEN=your_hf_token

# (Required) Specify the device to run the model on ('cpu' or 'hpu')
export LLM_DEVICE='cpu'

# (Optional) Proxy settings if applicable
export NO_PROXY=localhost,127.0.0.1
export HTTP_PROXY=
export HTTPS_PROXY=

# (Optional) Customize port and model before starting
export LLM_VLLM_MODEL_NAME="meta-llama/Llama-3-8B-Instruct"
export LLM_VLLM_PORT=8008

# Start the VLLM service
./run_vllm.sh
```

To verify that the LLM-as-a-Judge service is running by sending a test request:
```bash
model_name=$LLM_VLLM_MODEL_NAME ./query.sh
```

### Launch Service of Embeddings

_This step is required only for computing RAGAS metrics._

To calculate RAGAS metrics, a separate embedding service that provides vector representations of text is required. You can launch this service using existing scripts provided elsewhere in the project. 

To run the TEI embedding model server, navigate to the folder [src/comps/embeddings/impl/model-server/tei](../../../../../../src/comps/embeddings/impl/model-server/tei) and execute the script `run_tei.sh`. 

```bash
cd ../../../../../../src/comps/embeddings/impl/model-server/tei

# (Optional) Customize port and model before starting
export TEI_PORT=8090
export TEI_MODEL_NAME=BAAI/bge-large-en-v1.5

# Start the embedding service
./run_tei.sh
```

## Metrics

The following metrics evaluate different aspects of the Retrieval-Augmented Generation (RAG) system, covering document retrieval effectiveness, the quality of generated answers, and the faithfulness and grounding of responses.

| **Category**                        | **Metric**                       | **Description**                                                                                         | 
| ----------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Retrieval / Reranking**           |                                  | *These metrics assess how effectively the system retrieves relevant documents from the knowledge base.* |
|                                     | `Hits@K`                         | Proportion of queries with at least one relevant document in the top-K results                          |
|                                     | `MRR@K` (Mean Reciprocal Rank)   | Reflects how early the first relevant document appears in the top-K ranking                             |
|                                     | `MAP@K` (Mean Average Precision) | Average precision across all relevant documents in the top-K results                                    |
| | | | 
| **Generated Response (End-to-End)** |                                  | *These metrics evaluate the quality of the final answer produced by the full RAG pipeline.*             |
|                                     | `bleu-avg`, `bleu-1` to `bleu-4` | N-gram precision between generated and reference answers (BLEU-avg is the average of BLEU-n)            |
|                                     | `rouge-L`                        | Longest common subsequence between generated and reference texts                                        |
|                                     | `LLM-score`                      | Score given by a large language model acting as a judge of response quality — *Not implemented*         |
| | | | 
| **Faithfulness & QA (RAGAS)**       |                                  | *RAGAS metrics are designed to assess factual consistency and contextual grounding.*                    |
|                                     | `answer_correctness`             | Semantic correctness of the generated answer compared to the ground truth                               |
|                                     | `answer_relevancy`               | Degree to which the answer addresses the original question                                              |
|                                     | `semantic_similarity`            | Semantic similarity between generated and reference answer                                              |
|                                     | `context_precision`              | Precision of retrieved context supporting the answer                                                    |
|                                     | `context_recall`                 | Recall of relevant context in retrieved content                                                         |
|                                     | `faithfulness`                   | Degree to which the answer is grounded in the retrieved context (i.e., free from hallucinations)        |



## MultiHop (English dataset)

[MultiHop-RAG](https://arxiv.org/pdf/2401.15391) is a QA dataset to evaluate retrieval and reasoning across documents with metadata in the RAG pipelines. It contains *2556 queries*, with evidence for each query distributed across 2 to 4 documents. The queries also involve document metadata, reflecting complex scenarios commonly found in real-world RAG applications.

This evaluation uses [yixuantt/MultiHopRAG](https://huggingface.co/datasets/yixuantt/MultiHopRAG). Please note that queries labeled as `null_query`, where the expected answer is _"Insufficient information"_, are excluded from the evaluation.


### Evaluation

This section explains how to run the evaluation pipeline for Multihop dataset.

The evaluation script is located at `examples/eval_multihop.py`. 

To list all available arguments and their usage, run:

```bash
python eval_multihop.py --help
```


| **Argument**           | **Default Value**                   | **Description**                                                                             |
| ---------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------- |
| `--output_dir`         | `./output`                          | Directory to save evaluation results                                                        |
| `--dataset_path`       | `multihop_dataset/MultiHopRAG.json` | Path to the evaluation dataset                                                              |
| `--docs_path`          | `multihop_dataset/corpus.json`      | Path to the documents for retrieval                                                         |
| `--limits`             | `100`                               | Number of queries to evaluate (0 means evaluate all; default: 100)                          |
| `--ingest_docs`        | *(flag)*                            | Ingest documents into the vector database (use only on first run)                           |
| `--generation_metrics` | *(flag)*                            | Compute text generation metrics (`BLEU`, `ROUGE`)                                           |
| `--retrieval_metrics`  | *(flag)*                            | Compute retrieval metrics (`Hits@K`, `MAP@K`, `MRR@K`)                                      |
| `--ragas_metrics`      | *(flag)*                            | Compute RAGAS metrics (answer correctness, context precision, etc.)                         |
| `--resume_checkpoint`  | *None*                              | Path to a checkpoint file to resume evaluation from previous state                          |
| `--keep_checkpoint`    | *(flag)*                            | Keep the checkpoint file after evaluation (do not delete)                                   |
| `--llm_judge_endpoint` | `http://localhost:8008`             | URL of the LLM judge service; only used for RAGAS evaluation                                |
| `--embedding_endpoint` | `http://localhost:8090/embed`       | URL of the embedding service endpoint, only used for RAGAS                                  |
| `--temperature`        | 	Read from RAG system config        | Controls text generation randomness; defaults to RAG system setting if omitted.             |
| `--max_new_tokens`     |  Read from RAG system config        | Maximum tokens generated; defaults to RAG system setting if omitted.                        |


> Note: If `--dataset_path` and `--docs_path` are set to their default values and the corresponding files are not found locally, they will be automatically downloaded at runtime from [yixuantt/MultiHopRAG](https://huggingface.co/datasets/yixuantt/MultiHopRAG) and saved to the expected local paths.

> Note: For the first run, make sure to include the --ingest_docs flag to ingest documents into the vector database. For subsequent runs, this flag should be omitted to avoid re-ingesting.

### Usage Guide

This section outlines how to run Multihop evaluation of the RAG pipeline using [examples/eval_multihop.py](examples/eval_multihop.py).

 - **Ingest Documents**
 
    To ingest the MultiHop dataset into the RAG system, use the flag `--ingest_docs`:
    ```bash
    python eval_multihop.py --ingest_docs
    ```

  - **Evaluate Generated Answers**

    _Metrics: BLEU, ROUGE, (LLM-score – not implemented yet)_

    To evaluate the quality of RAG generated answers on Multihop queries, run:

    ```bash
    # First-time run (with document ingestion)
    python eval_multihop.py --ingest_docs --generation_metrics

    # Or if documents are already ingested
    python eval_multihop.py --generation_metrics

    # For a quick test, limit the number of evaluated queries
    python eval_multihop.py --generation_metrics --limits 2
    ```

  - **Evaluate Retrieval Quality**

    _Metrics: Hits@K, MAP@K, MRR@K_

    To evaluate the retrieval/reranking quality of the RAG system based on queries from the embedded MultiHop dataset, run:

    ```bash
    # First-time run (with document ingestion)
    python eval_multihop.py --ingest_docs --retrieval_metrics

    # Or if documents are already ingested
    python eval_multihop.py --retrieval_metrics

    # For a quick test, limit the number of evaluated queries
    python eval_multihop.py --retrieval_metrics --limits 2

    # For a run when you plan to continue later
    python eval_multihop.py --retrieval_metrics --limits 100 --keep_checkpoint

    # To resume a previous run (useful in case of failure or interruption)
    python eval_multihop.py --retrieval_metrics --limits 200 --resume_checkpoint ./output/multihop_YYYYMMDDHHMMSS.checkpoint.jsonl
    ```


  - **RAGAS Evaluation**

    _Metrics: answer_correctness, answer_relevancy, semantic_similarity,  context_precision, context_recall, faithfulness_

    ⚠️ For RAGAS evaluation, you must have two external services running: an LLM-as-a-Judge service and an embedding service — see the Run LLM-as-a-Judge and Embedding section for setup instructions..

    ```bash
    python eval_multihop.py --ragas_metrics \
    --llm_judge_endpoint http://<llm_host>:<port> \
    --embedding_endpoint http://<embedding_host>:<port>/embed
    ```


#### Example Output

Command:
```sh
python eval_multihop.py --ingest_docs --generation_metrics --limits 10
```
Exemplary Logs:
```sh
[2025-07-15 02:56:25,341] [    INFO] - [RAG Evaluator Multihop] - Running Multihop evaluation with arguments: {'dataset_path': 'multihop_dataset/MultiHopRAG.json', 'docs_path': 'multihop_dataset/corpus.json', 'output_dir': './output', 'temperature': 0.1, 'ingest_docs': False, 'retrieval_metrics': False, 'ragas_metrics': False, 'limits': 10}
[2025-07-15 02:56:27,748] [    INFO] - [RAG Evaluator] - EDP connection: OK
[2025-07-15 02:56:36,280] [    INFO] - [RAG Evaluator] - ChatQA connection: OK
[2025-07-15 02:56:36,282] [    INFO] - [RAG Evaluator Multihop] - Reading data from: multihop_dataset/corpus.json
[2025-07-15 02:56:36,312] [    INFO] - [RAG Evaluator Multihop] - Total corpus documents: 609
[2025-07-15 02:56:36,312] [    INFO] - [RAG Evaluator Multihop] - Reading data from: multihop_dataset/MultiHopRAG.json
[2025-07-15 02:56:36,336] [    INFO] - [RAG Evaluator Multihop] - Total queries in dataset: 2556
[2025-07-15 02:56:36,336] [    INFO] - [RAG Evaluator Multihop] - Filtering queries categorized as 'null_query' (insufficient information)...
[2025-07-15 02:56:36,336] [    INFO] - [RAG Evaluator Multihop] - Queries remaining: 2255
[2025-07-15 02:56:36,339] [    INFO] - [RAG Evaluator Multihop] - Limit applied. Using the first 10 queries for evaluation
[...]
[2025-07-15 02:58:08,827] [    INFO] - [RAG Evaluator] - Output saved to ./output/multihop_20250715025625.json
[2025-07-15 02:58:08,828] [    INFO] - [RAG Evaluator Multihop] - Evaluation overall: {'avg. bleu-avg': 0.00932488203650043, 'avg. bleu-1': 0.045125830426945665, 'avg. bleu-2': 0.025474525474525472, 'avg. bleu-3': 0.008511488511488512, 'avg. bleu-4': 0.005756578947368421, 'avg. rouge-L': np.float64(0.0744953998809568), 'avg. LLM-score': 0.0, 'avg. length': 322.7, 'num': 10}
```

The evaluation results are stored in the output/ directory with detailed logs and per-query metrics, where:
 - query: the actual question sent to the RAG pipeline,
 - ground_truth_text: the expected (gold) answer,
 - generated_text: the chat's answer.

The query and its corresponding ground_truth_text originate from the yixuantt/MultiHopRAG dataset.


## Acknowledgements
This example is mostly adapted from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) repo, we thank the authors for their great work!
