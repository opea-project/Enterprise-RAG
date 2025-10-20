# Document Summarization Microservice

This microservice, designed for Document Summarization, processes input consisting of documents or text content and generates concise summaries using large language models. The service takes documents as input, constructs appropriate prompts for summarization, and leverages [LLM microservice](../llms/README.md) inference to produce intelligent, context-aware summaries.

## Table of Contents

1. [Document Summarization Microservice](#document-summarization-microservice)
2. [Configuration Options](#configuration-options)
3. [Getting Started](#getting-started)
   - 3.1. [Prerequisite: Start LLM Microservice](#prerequisite-start-llm-microservice)
   - 3.2. [🚀 Start Document Summarization Microservice with Python (Option 1)](#-start-document-summarization-microservice-with-python-option-1)
     - 3.2.1. [Install Requirements](#install-requirements)
     - 3.2.2. [Start Microservice](#start-microservice)
   - 3.3. [🚀 Start Document Summarization Microservice with Docker (Option 2)](#-start-document-summarization-microservice-with-docker-option-2)
     - 3.3.1. [Build the Docker Image](#build-the-docker-image)
     - 3.3.2. [Run the Docker Container](#run-the-docker-container)
   - 3.4. [Verify the Document Summarization Microservice](#verify-the-document-summarization-microservice)
     - 3.4.1. [Check Status](#check-status)
     - 3.4.2. [Sending a Request](#sending-a-request)
       - 3.4.2.1. [Example Input](#example-input)
       - 3.4.2.2. [Example Output](#example-output)
4. [Additional Information](#additional-information)
   - 4.1. [Project Structure](#project-structure)
   - 4.2. [Tests](#tests)

## Configuration Options

The configuration for the Document Summarization Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `DOCSUM_USVC_PORT`              | The port of the microservice, by default 9001.                                                                        |
| `DOCSUM_DEFAULT_SUMMARY_TYPE`   | The default summarization strategy. Supported values: "map_reduce", "refine", "stuff". Default is "map_reduce".                |
| `DOCSUM_LLM_USVC_ENDPOINT`      | URL of the LLM microservice endpoint, e.g., "http://localhost:9000/v1"                                                |
| `OPEA_LOGGER_LEVEL`             | Log level for the microservice. Supported values: DEBUG, INFO, WARNING, ERROR. Default is INFO.                       |

## Summary types

The Document Summarization Microservice supports three different summarization strategies, based on those supported by Langchain:

- **(default) map_reduce**: Generates individual summaries for each chunk (map phase), then combines these summaries into a final summary (reduce phase). Ideal for large documents that exceed the context window. Provides comprehensive coverage but may lose some context between chunks.

- **stuff**: Concatenates all chunks into a single prompt and generates one summary. Best for small documents that fit within the model's context window. Simple and fast, but limited by number of tokens for one LLM request.

- **refine**: Processes chunks sequentially, refining the summary iteratively with each new document. Starts with a summary of the first chunk, then updates it based on the second chunk, and so on. Best for maintaining context and coherence across multiple related documents, but can be slower than `map_reduce`.

## Getting started

There're 2 ways to run this microservice:
  - [via Python](#-start-document-summarization-microservice-with-python-option-1)
  - [via Docker](#-start-document-summarization-microservice-with-docker-option-2) **(recommended)**

### Prerequisite: Start LLM Microservice

The Document Summarization Microservice interacts with a LLM microservice endpoint, which must be operational and accessible at the URL specified by the `DOCSUM_LLM_USVC_ENDPOINT` env. Feel free to use docker compose available in [impl/model_server/llm](impl/model_server/llm/) or set up the llm microservice yourself by using instructions in [LLM README](../llms/README.md).

> [!IMPORTANT]
> Docsum microservice uses OpenAI Client to connect to the LLM. Therefore, OpenAI API is required to run the pipeline correctly. To enable LLM with OpenAI API for streaming, run LLM with `LLM_OPENAI_FORMAT_STREAMING` set to `True`.

### 🚀 Start Document Summarization Microservice with Python (Option 1)

To start the Document Summarization microservice, you need to install python packages first.

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python opea_docsum_microservice.py
```

### 🚀 Start Document Summarization Microservice with Docker (Option 2)

#### Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../
docker build -t opea/docsum:latest -f comps/docsum/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### Run the Docker Container
```bash
docker run -d --name="docsum-microservice" \
  --net=host \
  --ipc=host \
  opea/docsum:latest
```

### Verify the Document Summarization Microservice

#### Check Status

```bash
curl http://localhost:9001/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### Sending a Request

> [!NOTE]
> Ensure that your llm microservice is running at `DOCSUM_LLM_USVC_ENDPOINT` and is ready to accept requests. Be aware that the server may take some time to become fully operational; otherwise, the docsum microservice will return an Internal Server Error.

##### Example Input

```bash
curl http://localhost:9001/v1/docsum \
        -X POST \
        -d '{
                "docs": [
                    {
                        "text": "Human history or world history is the record of humankind from prehistory to the present. Modern humans evolved in Africa around 300,000 years ago and initially lived as hunter-gatherers. They migrated out of Africa during the Last Ice Age and had spread across Earths continental land except Antarctica by the end of the Ice Age 12,000 years ago. Soon afterward, the Neolithic Revolution in West Asia brought the first systematic husbandry of plants and animals, and saw many humans transition from a nomadic life to a sedentary existence as farmers in permanent settlements. The growing complexity of human societies necessitated systems of accounting and writing. These developments paved the way for the emergence of early civilizations in Mesopotamia, Egypt, the Indus Valley, and China, marking the beginning of the ancient period in 3500 BCE. These civilizations supported the establishment of regional empires and acted as a fertile ground for the advent of transformative philosophical and religious ideas, initially Hinduism during the late Bronze Age, and – during the Axial Age: Buddhism, Confucianism, Greek philosophy, Jainism, Judaism, Taoism, and Zoroastrianism. The subsequent post-classical period, from about 500 to 1500 CE, witnessed the rise of Islam and the continued spread and consolidation of Christianity while civilization expanded to new parts of the world and trade between societies increased. These developments were accompanied by the rise and decline of major empires, such as the Byzantine Empire, the Islamic caliphates, the Mongol Empire, and various Chinese dynasties. This periods invention of gunpowder and of the printing press greatly affected subsequent history. During the early modern period, spanning from approximately 1500 to 1800 CE, European powers explored and colonized regions worldwide, intensifying cultural and economic exchange. This era saw substantial intellectual, cultural, and technological advances in Europe driven by the Renaissance, the Reformation in Germany giving rise to Protestantism, the Scientific Revolution, and the Enlightenment. By the 18th century, the accumulation of knowledge and technology had reached a critical mass that brought about the Industrial Revolution, substantial to the Great Divergence, and began the modern period starting around 1800 CE. The rapid growth in productive power further increased international trade and colonization, linking the different civilizations in the process of globalization, and cemented European dominance throughout the 19th century. Over the last 250 years, which included two devastating world wars, there has been a great acceleration in many spheres, including human population, agriculture, industry, commerce, scientific knowledge, technology, communications, military capabilities, and environmental degradation. The study of human history relies on insights from academic disciplines including history, archaeology, anthropology, linguistics, and genetics. To provide an accessible overview, researchers divide human history by a variety of periodizations."
                    }
                ],
                "summary_type": "refine",
                "stream": true
            }' \
        -H 'Content-Type: application/json'
```

##### Example Output

The following examples demonstrate the Document Summarization microservice output in both non-streaming and streaming modes.

- In **non-streaming mode** (stream=false), the service returns a single JSON response:

```json
{
  "id":"33e5c9ef38fd7c5daa8e4675d8050530",
  "text":"Here is a concise summary of human history:Human history began around 300,000 years ago in Africa, with modern humans migrating and spreading across the globe. Early civilizations emerged in Mesopotamia, Egypt, the Indus Valley, and China around 3500 BCE, giving rise to regional empires and philosophical and religious ideas. Over time, human history accelerated rapidly, with significant advancements in population, agriculture, industry, and technology, despite two devastating world wars.",
  "prompt":"",
  "stream":false,
  "choices":null,
  "output_guardrail_params":null,
  "data":null
}
```

- In **streaming mode** (stream=true), the response is sent in chunks, providing real-time updates for each word or phrase as it is generated:
```
data: Here
data:  is
data:  a
data:  concise
data:  summary
data:  of
data:  human
data:  history
data: :
data: Human
data:  history
data:  spans
data:
data: 300
data: ,
data: 000
data:  years
data: ,
data:  from
data:  emergence
data:  in
data:  Africa
data:  to
data:  the
data:  present
data: .
data:  Early
data:  humans
data:  migrated
data: [DONE]
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the Document Summarization microservice, including model servers integration and Dockerfiles.

- `utils/`: This directory contains utility scripts and modules used by the Document Summarization Microservice for document processing and summarization operations.

#### Tests
- `src/tests/unit/docsum/`: Contains unit tests for the Document Summarization Microservice components
