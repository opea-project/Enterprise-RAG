### Tests Prerequisites
In order to be able to run the e2e performance benchmark you need to:
* install necessary python packages
```bash
pip3 install -r requirements.txt
```
* configure `/etc/hosts`, so erag.com domain points to your eRAG deployment IP
* add your self signed TLS certificate to OS trusted store
```bash
sudo cp repo_path/deployment/tls.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates
```
* have a valid credentials inside `repo_path/deployment/default_credentials.txt`
* export your HF token `export HF_TOKEN="my-huggingface-token"`
* it is also advised to increase the rate limits for chatqa endpoint in `repo_path/deployment/components/apisix-routes/values.yaml` before eRAG installation to avoid ratelimiter errors (429 error code) - this can be done by modifying `rate_limit_count` value under `endpoint -> chatqa` section of the file

### Ingesting data into RAG
Before running the test it is advised to ingest some data into eRAG to ensure that vector database contains some real context data. In order to do so there is the script which will do that. It can take few hours to execute that part.

####
Please export `no_proxy` value so it would contain `erag.com` and `.erag.com`.

Next execute bellow script:

```bash
sudo -E ./prepare_1M_vectors.sh
```
Script will load around 40 000 vectors based on real documents which are context related with the queries executed by the test benchmark. Additionally, it will fill the database with the context of Simple English Wikipedia dump to achieve totally 1 000 000 of vectors. When testing using such a database we can simulate the production size databases and test the impact of data retrieval in eRAG pipeline.
### Test execution
In order to run the test you need to generate a file with valid User Access Tokens. There is a script do do that. Those tokens are valid for 10800 seconds (after tokens expiration eRAG is going to return 401 errors). You need to execute the number of token which is greater or equal to number of connections which you want to test for example:
```bash
sudo -E ./generate_uat_to_file.sh /opt/uat.txt 32
```
After that, you can run the benchmark. You need to specify the input file with test questions, length of the test, number of parallel connections and location of file with tokens. Also, it is suggested to specify the tokenizer model for benchmark, which would be the same as eRAG LLM model.
```bash
python3 benchmark.py -f questions-long.csv -d 30m -c 32 -b /opt/uat.txt -m Intel/neural-chat-7b-v3-3
```
When the test (or multiple tests for different parameters) are completed, detailed results for all the queries are saved into `bench_*.csv` files. You can parse them using the provided tool:
```bash
python3 parse.py .
```
