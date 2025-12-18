# Accuracy Tuning Tips

This guide provides recommendations for tuning the accuracy of your Intel® AI for Enterprise RAG deployment.

## Table of Contents

- [Overview](#overview)
- [Similarity Search with Siblings](#similarity-search-with-siblings)
- [Late Chunking](#late-chunking)
- [Accuracy Assessment and Monitoring](#accuracy-assessment-and-monitoring)

## Overview

In Retrieval-Augmented Generation (RAG) systems, the quality of generated answers depends on many interconnected factors, such as retriever configuration, prompt design, and LLM model selection. However, how well the most relevant, knowledge-rich document fragments are delivered to the LLM—is often the key driver of accuracy. This guide presents two advanced techniques that help deliver more informative and contextually relevant content to the LLM, improving the accuracy of generated answers:

1. **Similarity Search with Siblings** - Retrieving contextually related chunks around the matched results
2. **Late Chunking** - Embedding full documents prior to chunking to retain broader contextual meaning.

## Similarity Search with Siblings

### What is Siblings Retrieval?

When a chunk is identified as relevant through similarity search, the siblings method retrieves adjacent chunks (siblings) from the same document. This ensures that the retrieved context includes information that appears before and after the matched chunk, providing more complete and coherent information to the LLM.

### Benefits

- **Enhanced Context**: Provides surrounding information that may be crucial for understanding the matched chunk.
- **Improved Coherence**: Retrieved passages are more complete and easier for the LLM to comprehend.
- **Reduced Fragmentation**: Minimizes issues caused by chunk boundaries or insufficient overlap between chunks.

### Drawbacks

Since additional sibling chunks are included, more data is passed to the LLM, which increases processing load and affects performance, especially under high user concurrency. Overhead becomes more noticeable with larger chunk sizes. 

### How to enable it

Similarity search with siblings is available as a built-in search type in the vector store component. To enable it, configure the retriever to use `similarity_search_with_siblings` as the search type. This technique can be enabled or adjusted at runtime and configured directly from the Control Plane via the Admin Panel by modifying the retriever settings. Unlike late chunking, it does not require redeploying or re-ingesting documents, allowing you to fine-tune retrieval behavior on-the-fly.

For detailed information on configuring this feature, see the [Vector Store documentation](../src/comps/vectorstores/README.md#search).

## Late Chunking

### What is Late Chunking?

Traditional chunking splits documents into smaller pieces before embedding, which can lead to loss of contextual information. Late chunking reverses this approach.

**Traditional Approach**:
```
Document → Split into Chunks → Embed Each Chunk → Store Embeddings
```

**Late Chunking Approach**:
```
Document → Embed Full Document → Split into Chunks → Store Embeddings
```

Generating embeddings for the entire document or large sections is possible with models that support much longer token sizes (up to 8,192 tokens for jina-embeddings-v2-base-en). However, due to the limited input size constraints of LLMs, we still require vector representations of smaller text chunks. By delaying the chunking process, these smaller chunks contain more coherent and contextually related information.

For more details on the late chunking technique, read the article [Late Chunking in Long-Context Embedding Models](https://jina.ai/news/late-chunking-in-long-context-embedding-models/).

### Benefits

- **Contextual Embeddings**: Each chunk retains information from the large section, allowing for more accurate matching based on document-level context
- **Better Semantic Understanding**: Embeddings capture relationships between chunks
- **Improved Retrieval Quality**: More accurate matching based on document-level context
- **Reduced Ambiguity**: Context helps disambiguate terms that have different meanings in different contexts

### Drawbacks

Since full documents are embedded before chunking, the embedding phase takes longer and requires a model that supports long input sequences (e.g., jina-embeddings-v2-base-en). Larger embeddings limit opportunities for parallelization or delegating smaller chunks, and scaling improvements are effective only up to a certain point.

Additionally, the choice of late chunking must be made at deployment time. Switching to late chunking after documents have already been ingested requires re-embedding all previously ingested documents, because this technique fundamentally changes the structure of embeddings.

### How to enable it

To enable late chunking, edit your inventory `config.yaml` file:

1. **Update the embedding model** to use a model that supports longer token sequences:
   ```yaml
   embedding_model_name: "jinaai/jina-embeddings-v2-base-en"
   ```

2. **Enable late chunking** (disabled by default):
   ```yaml
   edp:
     late_chunking:
       enabled: true
   ```

3. **Run the installation** with the updated configuration by following the deployment steps in the [Application Deployment Guide](application_deployment_guide.md).


## Accuracy Assessment and Monitoring

To ensure the applied accuracy-enhancing technique is effective for your deployment, monitor both key quality pillars and performance metrics:

- **Retrieval Accuracy**: Regularly check that the system retrieves the most relevant chunks.
- **Answer Quality**: Evaluate the correctness and completeness of the responses generated by the system.
- **User Satisfaction**: Gather feedback and ratings to understand the user experience and guide improvements.
- **First Token Latency**: Tracks the time until the first token of the response is returned, reflecting responsiveness.
- **Response Time**: Measures total time to generate and deliver a complete response, showing overall system efficiency.

### Accuracy Evaluator

Intel® AI for Enterprise RAG includes a comprehensive Accuracy Evaluator for automated end-to-end testing using the MultiHop dataset (2,556 queries). It computes 10+ metrics including retrieval (Hits@K, MRR, MAP), generation (BLEU, ROUGE-L), and RAGAS metrics (Answer Correctness, Faithfulness, Context Precision/Recall).

For detailed setup and usage, see the [RAG Evaluation Guide](../src/tests/e2e/evals/evaluation/rag_eval/README.md).
