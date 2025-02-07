# Prompt Template Microservice

The Prompt Template Microservice is designed to dynamically generate prompt templates for large language models (LLMs). It allows users to customize the prompt format by specifying the context and question, ensuring that the generated prompts are tailored to the specific requirements of the application, and as the result enhance the interaction with LLMs by providing more relevant and context-aware prompts.


## Configuration Options
The configuration for the Prompt Template Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable        | Description                                                                |
|-----------------------------|----------------------------------------------------------------------------|
| `PROMPT_TEMPLATE_USVC_PORT`       | The port of the microservice, by default 7900                              |


## Getting started


### 🚀1. Start Prompt Template Microservice with Python (Option 1)

To start the Prompt Template Microservice, you need to install python packages first.

#### 1.1. Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

#### 1.2. Start Microservice

```bash
python opea_prompt_template_microservice.py
```

### 🚀2. Start Prompt Template Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/prompt_template:latest -f comps/prompt_template/impl/microservice/Dockerfile .
```

#### 2.2. Run the Docker Container
```bash
docker run -d --name="prompt-template-microservice" \
  --net=host \
  --ipc=host \
  opea/prompt_template:latest
```

### 3. Verify the Prompt Microservice

#### 3.1. Check Status

```bash
curl http://localhost:7900/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The `prompt_template` parameter allows you to specify a custom prompt template instead of using the [default one](utils/templates.py). The custom template must include placeholders that correspond to the input data fields to ensure validity and pass the validation checks. This feature provides greater flexibility and enables customization of prompts tailored to your specific requirements.

The output of the Prompt Template Microservice is a JSON object that contains the final prompt query, constructed using the specified prompt template and the values of the input data fields.


##### Case 1: Using the Default Prompt Template

When no custom prompt template is provided, the [default template](utils/templates.py) is automatically applied. This ensures that the system uses a standard structure for generating response for chat Q&A.

Example Request:

```bash
# use the default prompt template
curl http://localhost:7900/v1/prompt_template \
  -X POST \
  -d '{"data": {"initial_query":"What is Deep Learning?", "reranked_docs": [{"text":"Deep Learning is..."}]}, "prompt_template":""}' \
  -H 'Content-Type: application/json'
```

Output:

```json
{
  "id": "683f18c2d4dd30e2da5e6bcfaafe2258",
  "model": null,
  "query": "### You are a helpful, respectful, and honest assistant to help the user with questions. Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results: Deep Learning is... \n\n### Question: What is Deep Learning? \n\n### Answer:",
  "max_new_tokens": 1024,
  "top_k": 10,
  "top_p": 0.95,
  "typical_p": 0.95,
  "temperature": 0.01,
  "repetition_penalty": 1.03,
  "streaming": false,
  "input_guardrail_params": null,
  "output_guardrail_params": null
}
```

##### Case 2: Using a Custom Prompt Template
When a custom prompt template is provided, the system updates to use this template as the default for generating responses.

Example Request:
```bash
# use a custom prompt template
export PROMPT="### Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results: {reranked_docs} \n### Question: {initial_query} \n### Answer:"

curl http://localhost:7900/v1/prompt_template \
  -X POST \
  -d "{\"data\": {\"initial_query\":\"What is Deep Learning?\", \"reranked_docs\": [{\"text\":\"Deep Learning is...\"}]}, \"prompt_template\":\"${PROMPT}\"}" -H 'Content-Type: application/json'
```
Output:

```json
{
  "id": "6a8c89d33cc42f6a74c1cf0ebbfa3f85",
  "model": null,
  "query": "### Please refer to the search results obtained from the local knowledge base. But be careful to not incorporate information that you think is not relevant to the question. If you don't know the answer to a question, please don't share false information. ### Search results: Deep Learning is... \n### Question: What is Deep Learning? \n### Answer:",
  "max_new_tokens": 1024,
  "top_k": 10,
  "top_p": 0.95,
  "typical_p": 0.95,
  "temperature": 0.01,
  "repetition_penalty": 1.03,
  "streaming": false,
  "input_guardrail_params": null,
  "output_guardrail_params": null
}
```

##### Case 3: Using a Custom Prompt Template for a Specific Taks
In this case, the input data includes additional fields tailored for a translation task. A custom prompt template is defined to handle this task appropriately.

Example Request:

```bash
# define a custom prompt template for a specific task
export PROMPT="### You are a helpful, respectful, and honest assistant to help the user with translations. Translate this from {source_lang} to {target_lang}.\n### Question: {initial_query} \n### Answer:"

curl http://localhost:7900/v1/prompt_template \
  -X POST \
  -d "{\"data\": {\"initial_query\":\"什么是深度学习？\", \"source_lang\": \"chinese\", \"target_lang\": \"english\"},\"prompt_template\":\"${PROMPT}\"}" -H 'Content-Type: application/json'
```

Output:
```json
{
  "id": "d902648873a7ccab110014a9edb78677",
  "model": null,
  "query": "### You are a helpful, respectful, and honest assistant to help the user with translations. Translate this from chinese to english.\n### Question: 什么是深度学习？ \n### Answer:",
  "max_new_tokens": 1024,
  "top_k": 10,
  "top_p": 0.95,
  "typical_p": 0.95,
  "temperature": 0.01,
  "repetition_penalty": 1.03,
  "streaming": false,
  "input_guardrail_params": null,
  "output_guardrail_params": null
}
```


#### Tests
- `src/tests/unit/prompt_template/`: Contains unit tests for the Prompt Template Microservice components
