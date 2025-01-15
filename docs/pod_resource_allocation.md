Below table shows resources used to run EnterpriseRAG

| Namespace  | Pod Name | Reserved CPUs | Limit CPUs | Reserved Memory | Limit Memory | Comment |
|------------|----------|---------------|------------|-----------------|--------------|---------|
| dataprep   | dataprep | 8             | 8          | 16Gi            | 16Gi         | OMP_NUM_THREADS 8        |
| dataprep   | embedding-svc | 1             | 4          | 2Gi             | 4Gi          |         |
| dataprep    | ingestion-svc | 1             | 4          | 2Gi             | 2Gi          |         |
| chatqa   | embedding-svc | 1             | 4          | 2Gi             | 4Gi          |         |
| chatqa   | torchserve-embedding-svc| 1             | 4          | 4Gi             | 16Gi          | OMP_NUM_THREADS 4 , 4 replicas   |
| chatqa   | input-scan-svc | 4             | 8          | 8Gi             | 16Gi          |         |
| chatqa   | llm-svc| 1             | 4          | 2Gi             | 4Gi          |         |
| chatqa   | output-scan-svc| 4             | 8          | 8Gi             | 16Gi          |         |
| chatqa   | prompt-template-svc| 1             | 4          | 2Gi             | 4Gi          |         |
| chatqa   | redis-vector-db| 1             | 4          | 2Gi             | 8Gi          |         |
| chatqa   | reranking-svc| 1             | 4          | 2Gi             | 2Gi          |         |
| chatqa   | tei-reranking-svc | 2             | 8          | 16Gi             | 32Gi          |         |
| chatqa   | vllm         | 32             | 32          | 64Gi             | 100Gi          | OMP_NUM_THREADS to 32   |
| chatqa   | retriever-svc| 1             | 4          | 2Gi             | 2Gi          |         |



