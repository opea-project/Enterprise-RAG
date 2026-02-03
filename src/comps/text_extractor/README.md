# Text Extractor Microservice

This microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to text_splitter microservice for splitting into chunks and, later, to embedding microservice in order to ultimately persist in the system.

## Table of Contents

1. [Text Extractor Microservice](#text-extractor-microservice)
2. [Support Matrix](#support-matrix)
3. [Configuration Options](#configuration-options)
4. [Getting Started](#getting-started)
   - 4.1. [🚀 Start Text Extractor Microservice with Python (Option 1)](#-start-text-extractor-microservice-with-python-option-1)
     - 4.1.1. [Install Requirements](#install-requirements)
     - 4.1.2. [Start Microservice](#start-microservice)
   - 4.2. [🚀 Start Text Extractor Microservice with Docker (Option 2)](#-start-text-extractor-microservice-with-docker-option-2)
     - 4.2.1. [Build the Docker service](#build-the-docker-service)
     - 4.2.2. [Run the Docker container](#run-the-docker-container)
   - 4.3. [Verify the Text Extractor Microservice](#verify-the-text-extractor-microservice)
     - 4.3.1. [Example input](#example-input)
       - 4.3.1.1. [File(s) Text Extractor](#files-text-extractor)
       - 4.3.1.2. [Link(s) Text Extractor](#links-text-extractor)
     - 4.3.2. [Example output](#example-output)
5. [Additional Information](#additional-information)
   - 5.1. [Project Structure](#project-structure)
     - 5.1.1. [Tests](#tests)

## Support Matrix

Supported files that Text Extractor can extract data from:

| File Extension | Loader Class                                                                 |
|----------------|------------------------------------------------------------------------------|
| AsciiDoc       | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| doc            | [LoadDoc](./utils/file_loaders/load_doc.py)                                  |
| docx           | [LoadDoc](./utils/file_loaders/load_doc.py)                                  |
| txt            | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| json           | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| jsonl          | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| csv            | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| xlsx           | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| xls            | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| pdf            | [LoadPdf](./utils/file_loaders/load_pdf.py)                                  |
| html           | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| md             | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| xml            | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| yaml           | [LoadWithMarkitdown](./utils/file_loaders/load_with_markitdown.py)           |
| ppt            | [LoadPpt](./utils/file_loaders/load_ppt.py)                                  |
| pptx           | [LoadPpt](./utils/file_loaders/load_ppt.py)                                  |
| tiff           | [LoadImage](./utils/file_loaders/load_image.py)                              |
| jpg            | [LoadImage](./utils/file_loaders/load_image.py)                              |
| jpeg           | [LoadImage](./utils/file_loaders/load_image.py)                              |
| png            | [LoadImage](./utils/file_loaders/load_image.py)                              |
| svg            | [LoadImage](./utils/file_loaders/load_image.py)                              |
| mp3*           | [LoadAudio](./utils/file_loaders/load_audio.py)                              |
| wav*           | [LoadAudio](./utils/file_loaders/load_audio.py)                              |

> [!NOTE]
> *Audio files (MP3, WAV) are only supported when `ASR_MODEL_SERVER_ENDPOINT` is configured. The audio files are transcribed using the ASR (Automatic Speech Recognition) microservice. Feel free to utilize [ASR microservice](../asr/) to extract data from audio files.

If you consider adding additional file support, implement it based on `AbstractLoader` class
and include that class into the `FileParser`'s `default_mappings` map.

Dataprep uses both `libmagic` and file extension to determine the file type. Both have to match to be processed.

> [!NOTE]
> AsciiDoc documents are being converted to HTML format with usage of [Asciidoctor](https://github.com/asciidoctor/asciidoctor) before being divided into chunks.

## Configuration options

Configuration is currently done via environment variables.

| Environment Variable             | Default Value             | Description                                                                                      |
|----------------------------------|---------------------------|--------------------------------------------------------------------------------------------------|
| `OPEA_LOGGER_LEVEL`              | `INFO`                    | Microservice logging output level                                                                |
| `TEXT_EXTRACTOR_USVC_PORT`             | `9398`              | (Optional) Text Extractor microservice port                                                            |
| `UPLOAD_PATH`                    | `/tmp/opea_upload`        | Path to where the data is saved                                                                  |
| `ASR_MODEL_SERVER_ENDPOINT`      | Not set                   | (Optional) URL of the ASR microservice endpoint for MP3/WAV support (e.g., `http://localhost:9009`) |
| `CRAWLER_HTTP_TIMEOUT`           | `60`                      | Timeout in seconds for HTTP requests made by the crawler                                         |
| `CRAWLER_MAX_RETRIES`            | `1`                       | Maximum number of request retries for downloading links                                          |
| `CRAWLER_HEADERS`                | `{}`                      | JSON encoded headers for requests. If not defined default headers are used                       |
| `CRAWLER_MAX_FILE_SIZE_MB`       | `128`                     | Maximum file size that is allowed to be downloaded while processing links in MB                  |

By default, files are saved to a directory under this container. Save path can be changed by setting the `UPLOAD_PATH` environment variable. It is advised to mount an additional volume for the files saved by Text Extractor. Files are persisted as a point in time reference to the data that is embedded and ultimately ingested into the vector database.

## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

There're 2 ways to run this microservice:
  - [via Python](#-start-text-extractor-microservice-with-python-option-1)
  - [via Docker](#-start-text-extractor-microservice-with-docker-option-2) **(recommended)**


### 🚀 Start Text Extractor Microservice with Python (Option 1)

#### Install Requirements
To freeze the dependencies of a particular microservice, [uv](https://github.com/astral-sh/uv) project manager is utilized. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml --extra cpu
source impl/microservice/.venv/bin/activate
```

#### Start Microservice

```bash
python opea_text_extractor_microservice.py
```

### 🚀 Start Text Extractor Microservice with Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the Docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/text_extractor:latest -f comps/text_extractor/impl/microservice/Dockerfile .
```

#### Run the Docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

> [!IMPORTANT]
> Add `--net=host` if you're using ASR_MODEL_SERVER_ENDPOINT.

```bash
docker run -d --name="text_extractor" --env-file comps/text_extractor/impl/microservice/.env -p 9398:9398 opea/text_extractor:latest
```

### Verify the Text Extractor Microservice
#### Example input

Text Extractor microservice as an input accepts a json containing links or files encoded in base64. Example requests can be found in followings paragraphs. It is possible to post both files and a list of link in one request.

##### File(s) Text Extractor

Files have to be encoded into Base64. This cURL format allows sending more data than using `-d`.

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:9398/v1/text_extractor <<JSON_DATA
{
  "files": [
    {
      "filename": "output.mp3",
      "data64": "$(base64 -w 0 output.mp3)"
    }
  ]
}
JSON_DATA
```

##### Link(s) Text Extractor

```bash
curl http://localhost:9398/v1/text_extractor \
  -X POST -H 'Content-Type: application/json' \
  -d '{ "links": ["https://example.com/"] }'
```

##### Text(s) Text Extractor

```bash
curl http://localhost:9398/v1/text_extractor \
  -X POST -H 'Content-Type: application/json' \
  -d '{ "texts": ["Human history or world history is the record of humankind from prehistory to the present. Modern humans evolved in Africa around 300,000 years ago and initially lived as hunter-gatherers. They migrated out of Africa during the Last Ice Age and had spread across Earths continental land except Antarctica by the end of the Ice Age 12,000 years ago. Soon afterward, the Neolithic Revolution in West Asia brought the first systematic husbandry of plants and animals, and saw many humans transition from a nomadic life to a sedentary existence as farmers in permanent settlements. The growing complexity of human societies necessitated systems of accounting and writing. These developments paved the way for the emergence of early civilizations in Mesopotamia, Egypt, the Indus Valley, and China, marking the beginning of the ancient period in 3500 BCE. These civilizations supported the establishment of regional empires and acted as a fertile ground for the advent of transformative philosophical and religious ideas, initially Hinduism during the late Bronze Age, and – during the Axial Age: Buddhism, Confucianism, Greek philosophy, Jainism, Judaism, Taoism, and Zoroastrianism. The subsequent post-classical period, from about 500 to 1500 CE, witnessed the rise of Islam and the continued spread and consolidation of Christianity while civilization expanded to new parts of the world and trade between societies increased. These developments were accompanied by the rise and decline of major empires, such as the Byzantine Empire, the Islamic caliphates, the Mongol Empire, and various Chinese dynasties. This periods invention of gunpowder and of the printing press greatly affected subsequent history. During the early modern period, spanning from approximately 1500 to 1800 CE, European powers explored and colonized regions worldwide, intensifying cultural and economic exchange. This era saw substantial intellectual, cultural, and technological advances in Europe driven by the Renaissance, the Reformation in Germany giving rise to Protestantism, the Scientific Revolution, and the Enlightenment. By the 18th century, the accumulation of knowledge and technology had reached a critical mass that brought about the Industrial Revolution, substantial to the Great Divergence, and began the modern period starting around 1800 CE. The rapid growth in productive power further increased international trade and colonization, linking the different civilizations in the process of globalization, and cemented European dominance throughout the 19th century. Over the last 250 years, which included two devastating world wars, there has been a great acceleration in many spheres, including human population, agriculture, industry, commerce, scientific knowledge, technology, communications, military capabilities, and environmental degradation. The study of human history relies on insights from academic disciplines including history, archaeology, anthropology, linguistics, and genetics. To provide an accessible overview, researchers divide human history by a variety of periodizations."] }'
```

#### Example output

For both files and links the output has the same format, containg the extracted text.

```json
{
  "loaded_docs":[
    {
      "text":"Example DomainThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.More information...",
      "metadata":{
        "url":"https://example.com/",
        "filename":"index.html",
        "timestamp":1748520579.4694135
      }
    }
  ]
}
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the Text Extractor microservice, including Dockerfile.

- `utils/`: This directory contains utility scripts and modules used by the Text Extractor Microservice.

#### Tests
- `src/tests/unit/text_extractor/`: Contains unit tests for the Text Extractor Microservice components
