# Intel® AI for Enterprise RAG E2E benchmark
### Deploy Enterprise RAG and Adjust the parameters
Before running the E2E benchmark, ensure that Enterprise RAG is deployed and configured with the recommended parameters as outlined in the [Performance tuning tips](../../../../docs/performance_tuning_tips.md) guide.

### Test prerequisites
In order to be able to run the e2e performance benchmark you need to:
* install necessary python packages
```bash
pip3 install -r requirements.txt
```
* bash scripts assumes that eRAG is deployed under `erag.com` domain:
  * if you are using the domain different than `erag.com` one you can overwrite it with `ERAG_DOMAIN_NAME` environmental variable
  * this variable has the impact on all the bash helpers
  * for python based benchmark see the relevant section to specify your domain
* benchmark and the bash helpers rely only on https protocol and can be run from any machine with https connection to eRAG, so you need to ensure that you have network (https) access to `erag.com` (or your own eRAG domain):
  * configure `/etc/hosts`, so `erag.com` domain and subdomains points to your eRAG deployment IP, for example: `127.0.0.1 minio.erag.com grafana.erag.com s3.erag.com erag.com auth.erag.com`
  * export both `no_proxy` and `NO_PROXY` env variables, so they contain  `erag.com` and `.erag.com` domains
* download TLS certificate for eRAG and add it as trusted local CA authority (otherwise failures due to self signed certificates can occur):
```bash
sudo -E ./add_cert_to_ca.sh
```
* export UI username and password of the account with administrative rights using `KEYCLOAK_ERAG_ADMIN_USERNAME` and `KEYCLOAK_ERAG_ADMIN_PASSWORD` env variables:
  * if username is not exported, then `erag-admin` will be used as default, but you still need to export the password
  * if you didn't change the default UI password after the ansible based installation you can export it using the default credentials file `source ../../../../deployment/ansible-logs/default_credentials.txt && export KEYCLOAK_ERAG_ADMIN_PASSWORD=$KEYCLOAK_ERAG_ADMIN_PASSWORD`
* export Realm username and password using `KEYCLOAK_REALM_ADMIN_USERNAME` and `KEYCLOAK_REALM_ADMIN_USERNAME` env variables:
  * if username is not exported, then `admin` will be used as default, but you still need to export the password
  * if you didn't change the default Realm password after the ansible based installation you can export it using the default credentials file `export KEYCLOAK_REALM_ADMIN_PASSWORD=$(cat ../../../../deployment/ansible-logs/default_credentials.yaml | grep KEYCLOAK_REALM_ADMIN_PASSWORD | awk '{print $2}')`
* if you are running test on Gaudi:
  * it is advised to increase the rate limits for chatqa endpoint in `/deployment/components/apisix-routes/values.yaml` before eRAG installation to avoid ratelimiter errors (429 error code) - this can be done by modifying `rate_limit_count` value under `endpoint -> chatqa` section of the file
  * vLLM warmup should not be skipped `VLLM_SKIP_WARMUP: "false"` for your LLM model in resource file `/deployment/pipelines/chatqa/resources-model-hpu.yaml`
  * for vector database (Redis) it is suggested to use `HNSW` algorithm instead of `FLAT`, results can be a little less accurate, but the retrieval latency for hundreds of parallel users will be smaller, this can be changed using `VECTOR_ALGORITHM` parameter in `/src/comps/retrievers/impl/microservice/.env` and `/deployment/components/edp/values.yaml`
* if you are using eRAG with gated huggingface LLM model:
  * export your HF token `export HF_TOKEN="my-huggingface-token"`
  * this is required for the python based benchmark, so it would be able to obtain proper tokenizer from huggingface

### Ingesting data into RAG
Before running the test, it is advised to ingest some data into eRAG to ensure that vector database contains some real context data. To do so there is the script which will do that. It can take few hours to execute that part.

```bash
./prepare_1M_vectors.sh
```
Script will load around 55 000 vectors based on real documents which are context related with the queries executed by the test benchmark. Additionally, it will fill the database with the context of Simple English Wikipedia dump to achieve totally 1 000 000 of vectors. When testing using such a database, we can simulate the production size databases and test the impact of data retrieval in eRAG pipeline.

Also, there is a possibility to create smaller database (it will load a context of real documents anyway, so around 55 000 of vectors, but won't be loading the parts of the Wikipedia dumps when `$TARGET_VECTORS` value is reached), then you need to specify the desired number of vectors as the parameter to the script:
```bash
./prepare_1M_vectors.sh $TARGET_VECTORS
```
If you have some other vectors and you want to delete them before filling the database using above script, there is also the helper to do so. Be careful with calling this helper, because it will delete all the entries in your vector database. Since vectors removing process is asynchronous, it is suggested to wait a while after running the script before filling the database with the new vectors.
```bash
./prepare_cleanup_vectors.sh
```

### Test execution
To run the test, you need to generate a file with valid User Access Tokens. There is a script to do that. Those tokens are valid for 10800 seconds (after tokens expiration eRAG is going to return 401 errors). You need to generate the number of token which is greater or equal to number of connections which you want to test, here is the example for 32 connections:
```bash
./generate_uat_to_file.sh /tmp/uat.txt 32
```
After that, you can run the benchmark. You need to specify the following parameters:
* input file with test questions `-f questions-pubmed.csv`
* length of the test `-d 30m`
* number of parallel connections(Concurrency levels) `-c 32`
* location of file with tokens `-b /tmp/uat.txt`
* the tokenizer model for benchmark, which would be the same as eRAG LLM model `-m meta-llama/Llama-3.1-8B-Instruct`
* (if you want to test with fixed number of input question tokens) specify the expected number of tokens `-x 512`
* (if you are running domain different than 'erag.com') specify the eRAG url `-s "https://${ERAG_DOMAIN_NAME}/api/v1/chatqna"`
```bash
python3 benchmark.py -f questions-pubmed.csv -d 30m -c 32 -b /tmp/uat.txt -m meta-llama/Llama-3.1-8B-Instruct
```
When the test (or multiple tests for different parameters) are completed, detailed results for all the queries are saved into `bench_*.csv` files. You can parse them using the provided tool:
```bash
python3 parse.py .
```

### Regenerating questions from PubMed data
By default `questions-pubmed.csv` file contains 1024 randomly generated questions based on [pubmed23n0001](https://huggingface.co/datasets/MedRAG/pubmed/tree/main/chunk) data. If you want to generate different set of questions based on that dataset, there is a script to do so. More details are described in help of it.
```bash
python3 generate_pubmed_questions.py --help
```

### Helpers for configuring eRAG
Some of the eRAG parameters have a significant impact on the performance, so in order to change them without logging into UI, there are some helpers to change those parameters using bash scripts:
* configuring `k` for retriever (number of documents retrieved from vector database)
```bash
./prepare_change_retriever.sh $TOP_N
```
* configuring `top_n` for reranker (number of output documents after reranking, which are appended into the prompt)
```bash
./prepare_change_reranker.sh $K
```
* configuring `max_new_tokens` for llm (number of output tokens in eRAG response)
```bash
./prepare_change_num_tokens.sh $MAX_NEW_TOKENS
```

### Performance testing best practices
* Adjusting resources:
  * If you are running configuration with HPA enabled, you need to first execute a warm-up run in order to allow HPA to scale the number of replicas of particular pods. Such a warm-up run should generally use the most stressing configuration you want to test and result of such a warm-up run should be voided.
  * If you are running configuration without HPA, it is suggested to adjust the particular nodes resources manually as described below:
    * vLLM pods scaling on Gaudi:
      * depending on LLM model every vLLM pod uses 1, 2, 4 Gaudi cards (tensor parallel parameter), so if you have a system with more cards (typically 8 cards) you can scale the number of replicas to use all of the cards in system
      * scaling can be done using following command `kubectl scale --replicas=$VLLM_REPLICAS -n chatqa deployment vllm-gaudi-svc-deployment`
    * vLLM pods scaling on Xeon:
      * if you are running baremetal system with multiple sockets you should generally create as many replicas of vLLM as many sockets you have
      * if you are running high core count systems (like 96 or 128 physical cores per socket) you can try to scale vLLM even more and create 2 or 3 vLLM instances per socket
      * scaling can be done using following command `kubectl scale --replicas=$VLLM_REPLICAS -n chatqa statefulset vllm-service-m-deployment`
    * TEI rereranking pod scaling:
      * if you are running on Xeon and there are still some free cores available it is suggested to scale TEI reranking pod to more than one replica (for example: 2)
      * if you are running on Gaudi with hundreds of parallel connections then it is suggested to scale TEI reranking pod to have 4, 8, or more replicas (depending on number of free resources)
      * scaling can be done using following command `kubectl scale --replicas=$TEI_REPLICAS -n chatqa deployment tei-reranking-svc-deployment`
    * Other pods typically do not cause a noticeable performance bottlenecks, but it is advised to observe the telemetry to notice any potential slowness of particular pods
* Test parameters:
  * Some of the previously mentioned eRAG configuration parameters, such as `k`, `top_n` and `max_new_tokens` are the main factors impacting the overall performance. Generally, you should use the parameters which match your expected configuration, but here are some of the scenarios which are commonly used to track the performance and compare it against the typical LLM benchmarks:
    * `k=10, top_n=7, max_new_tokens=1024` simulates 1024 input and 1024 output for LLM
    * `k=4, top_n=2, max_new_tokens=128` simulates 512 input and 128 output for LLM
    * `k=20, top_n=15, max_new_tokens=128` simulates 2048 input and 128 output for LLM
  * Number of parallel connections simulates the number of concurrent users using eRAG system. It should be configured to match the expected numbers of user in the system. Also, it is advised to swipe over the lower numbers of connections to understand how system will behave with a lower utilization, for example:
    * `1, 4, 8, 16, 32` for Xeon pipeline
    * `64, 128, 256, 512` for Gaudi pipeline
* Results file analysis:
  * For ChatQA eRAG application with streaming enabled there are two main metrics which should be analyzed to understand the system performance:
    * `first_token_lat_mean` reported in seconds and expected to be in range of few seconds, it describes how long user will wait for the first token to pop up as the response
    * `next_token_lat_mean` reported in seconds and expected to be in range of tens of milliseconds, it describes how long user will wait for the next tokens to be returned
