# Metric Card for RAGAS

Toolkit: https://github.com/explodinggradients/ragas


## Metric Description
RAGAS (Retrieval-Augmented Generation Assessment Scores) is a set of metrics for evaluating the quality of Retrieval-Augmented Generation (RAG) pipelines. Unlike traditional metrics like BLEU or ROUGE, RAGAS is designed specifically for assessing the interplay between retrieved context, generated answers, and ground-truth references. It includes both retrieval-level and generation-level evaluations and provides a holistic picture of a system's performance in open-domain QA and similar tasks.

The core metrics include:

 - **Answer Correctness** – measures whether the generated answer is factually correct with respect to the ground-truth reference, typically judged by an LLM.

 - **Answer Relevancy** – evaluates how relevant the generated answer is to the reference answer using semantic similarity.

 - **Semantic Similarity** – quantifies how semantically close the generated answer is to the ground-truth reference using dense embeddings.

 - **Context Precision** – measures how much of the retrieved context is actually relevant to the question.

 - **Context Recall** – captures how much relevant information (from the ideal context) is retrieved.

 - **Faithfulness** – measures how much of the answer content is grounded in the retrieved context; this helps detect hallucinations.

These metrics rely on embedding-based similarity (e.g., cosine similarity over sentence embeddings), and a large language model (LLM) acting as a judge for subjective evaluations such as faithfulness and answer correctness.

## How to Use

Please wrap your input data in `datasets.Dataset` class where each sample includes a question, retrieved contexts, the model’s answer, and a reference (ground-truth) answer.

```python3
from datasets import Dataset

example = {
    "question": "Who is wife of Barak Obama",
    "contexts": [
        "Michelle Obama, wife of Barak Obama (former President of the United States of America) is an attorney",
        "Barak and Michelle Obama have 2 daughters - Malia and Sasha",
    ],
    "answer": "Michelle Obama",
    "ground_truth": "Wife of Barak Obama is Michelle Obama",
}
dataset = Dataset.from_list([example])
```

## Launch LLM

Please follow instructions in section [../rag_eval/README.md](../../rag_eval/README.md#launch-service-of-llm-as-a-judge) to launch LLM as a judge with your desired LLM such as `meta-llama/Llama-3-8B-Instruct`. 

```python3
# note - if you wish to use answer relevancy metric, please set the embedding parameter

from langchain_community.embeddings import HuggingFaceBgeEmbeddings

embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-base-en-v1.5")

from ragas import RagasMetric

ragas_metric = RagasMetric(
    threshold=0.5, 
    model="<your LLM-as-a-judge endpoint URL here>",
    embeddings=embeddings
)
print(ragas_metric.measure(dataset))
```

### Output Values

Each metric returns a float score between 0 and 1.

Output Example:
```python
{
    'answer_correctness': 0.5652, 
    'answer_relevancy': 0.6491, 
    'semantic_similarity': 0.5062, 
    'context_precision': 0.4345, 
    'context_recall': 0.4798, 
    'faithfulness': 0.5431
}
```
