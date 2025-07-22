# Evaluation Methodology

<!-- TOC -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [MultiHop (English dataset)](#multihop-english-dataset)
  - [Evaluation](#evaluation)
- [CRUD (Chinese dataset)](#crud-chinese-dataset)
- [Acknowledgements](#acknowledgements)


<!-- /TOC -->

## Introduction

Retrieval-Augmented Generation (RAG) has recently gained traction in natural language processing. Numerous studies and real-world applications are leveraging its ability to enhance generative models through external information retrieval.

For evaluating the accuracy of a RAG pipeline, we use 2 latest published datasets and 10+ metrics which are popular and comprehensive:

- Dataset
  - [MultiHop](https://arxiv.org/pdf/2401.15391) (English dataset)
  - [CRUD](https://arxiv.org/abs/2401.17043) (Chinese dataset) _(Not yet implemented)_
- metrics (measure accuracy of both the context retrieval and response generation)
  - evaluation for retrieval/reranking _(Not yet implemented)_
    - MRR@10
    - MAP@10
    - Hits@10
    - Hits@4
    - LLM-as-a-Judge
  - evaluation for the generated response from the end-to-end pipeline
    - BLEU
    - ROUGE(L)
    - LLM-as-a-Judge _(Not yet implemented)_


## Prerequisites

 - It is recommended to use Python virtual environments to manage dependencies. You can set it up as follow:

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

 - Export the `PYTHONPATH` environment variable pointing to the `src` folder in this repository to ensure proper module resolution

 - A running RAG service must be accessible locally. If your system uses a proxy, ensure the no_proxy environment variable includes the following to allow local access without proxying:

    ```sh
    export no_proxy=localhost,127.0.0.1,erag.com,s3.erag.com
    ```

## MultiHop (English dataset)

[MultiHop-RAG](https://arxiv.org/pdf/2401.15391): a QA dataset to evaluate retrieval and reasoning across documents with metadata in the RAG pipelines. It contains *2556 queries*, with evidence for each query distributed across 2 to 4 documents. The queries also involve document metadata, reflecting complex scenarios commonly found in real-world RAG applications.

This evaluation uses [yixuantt/MultiHopRAG](https://huggingface.co/datasets/yixuantt/MultiHopRAG). Please note that queries labeled as `null_query`, where the expected answer is _"Insufficient information"_, are excluded from the evaluation.


### Evaluation

Use below command to run the evaluation, please note that for the first run, argument `--ingest_docs` should be added in the command to ingest the documents into the vector database, while for the subsequent run, this argument should be omitted.

```bash
python examples/eval_multihop.py --ingest_docs
```

If you just want a quick test run, use `--limits` to reduce the number of queries. For example:

```bash
python examples/eval_multihop.py --ingest_docs --limits 2
```


| Argument              | Default Value                       | Description                                                            |
| --------------------- | ----------------------------------- | ---------------------------------------------------------------------- |
| `--output_dir`        | `./output`                          | Directory to save evaluation results                                   |
| `--temperature`       | `0.1`                               | Controls the randomness of the model's text generation                 |
| `--dataset_path`      | `multihop_dataset/MultiHopRAG.json` | Path to the evaluation dataset                                         |
| `--docs_path`         | `multihop_dataset/corpus.json`      | Path to the documents for retrieval                                    |
| `--limits`             | 100                                | Number of examples to be evaluated                                     |
| `--ingest_docs`       | *(flag)*                            | Ingest documents into the vector database (use only for the first run) |
| `--retrieval_metrics` | *(flag)*                            | Compute retrieval metrics (Not implemented yet)                        |
| `--ragas_metrics`     | *(flag)*                            | Compute RAGAS metrics (Not implemented yet)                            |


> Note: If `--dataset_path` and `--docs_path` are set to their default values and the corresponding files are not found locally, they will be automatically downloaded at runtime from [yixuantt/MultiHopRAG](https://huggingface.co/datasets/yixuantt/MultiHopRAG) and saved to the expected local paths.

You can check arguments details use below command:
```bash
python examples/eval_multihop.py --help
```


#### Sample Execution And Output Overview

Command:
```sh
python eval_multihop.py --ingest_docs --limits 10
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
[2025-07-15 02:58:08,828] [    INFO] - [RAG Evaluator Multihop] - Evaluation overall: {'avg. bleu-avg': 0.00932488203650043, 'avg. bleu-1': 0.045125830426945665, 'avg. bleu-2': 0.025474525474525472, 'avg. bleu-3': 0.008511488511488512, 'avg. bleu-4': 0.005756578947368421, 'avg. rouge-L': np.float64(0.0744953998809568), 'avg. LLM-score': 0.0, 'avg. length': 322.7, 'num': 10, 'accuracy': 0.5}
```

The evaluation results are stored in the output/ directory with detailed logs and per-query metrics, where:
 - query: the actual question sent to the RAG pipeline,
 - ground_truth_text: the expected (gold) answer,
 - generated_text: the chat's answer.

The query and its corresponding ground_truth_text originate from the yixuantt/MultiHopRAG dataset.


## CRUD (Chinese dataset)

TBD

## Acknowledgements
This example is mostly adapted from [MultiHop-RAG](https://github.com/yixuantt/MultiHop-RAG) and [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) repo, we thank the authors for their great work!
