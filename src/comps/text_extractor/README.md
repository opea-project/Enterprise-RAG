# Text Extractor Microservice

This microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to text_splitter microservice for splitting into chunks and, later, to embedding microservice in order to ultimately persist in the system.

## Support Matrix

Supported files that Text Extractor can extract data from:

| File Extension | Loader Class                                                                 |
|----------------|------------------------------------------------------------------------------|
| AsciiDoc       | [LoadAsciiDoc](./utils/file_loaders/load_adoc.py)                            |
| doc            | [LoadDoc](./utils/file_loaders/load_doc.py)                                  |
| docx           | [LoadDoc](./utils/file_loaders/load_doc.py)                                  |
| txt            | [LoadTxt](./utils/file_loaders/load_txt.py)                                  |
| json           | [LoadJson](./utils/file_loaders/load_json.py)                                |
| jsonl          | [LoadJson](./utils/file_loaders/load_json.py)                                |
| csv            | [LoadCsv](./utils/file_loaders/load_csv.py)                                  |
| xlsx           | [LoadXls](./utils/file_loaders/load_xls.py)                                  |
| xls            | [LoadXls](./utils/file_loaders/load_xls.py)                                  |
| pdf            | [LoadPdf](./utils/file_loaders/load_pdf.py)                                  |
| html           | [LoadHtml](./utils/file_loaders/load_html.py)                                |
| md             | [LoadMd](./utils/file_loaders/load_md.py)                                    |
| xml            | [LoadXml](./utils/file_loaders/load_xml.py)                                  |
| yaml           | [LoadYaml](./utils/file_loaders/load_yaml.py)                                |
| ppt            | [LoadPpt](./utils/file_loaders/load_ppt.py)                                  |
| pptx           | [LoadPpt](./utils/file_loaders/load_ppt.py)                                  |
| tiff           | [LoadImage](./utils/file_loaders/load_image.py)                              |
| jpg            | [LoadImage](./utils/file_loaders/load_image.py)                              |
| jpeg           | [LoadImage](./utils/file_loaders/load_image.py)                              |
| png            | [LoadImage](./utils/file_loaders/load_image.py)                              |
| svg            | [LoadImage](./utils/file_loaders/load_image.py)                              |

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
| `CRAWLER_HTTP_TIMEOUT`           | `60`                      | Timeout in seconds for HTTP requests made by the crawler                                         |
| `CRAWLER_MAX_RETRIES`            | `1`                       | Maximum number of request retries for downloading links                                          |
| `CRAWLER_HEADERS`                | `{}`                      | JSON encoded headers for requests. If not defined default headers are used                       |
| `CRAWLER_MAX_FILE_SIZE_MB`       | `128`                     | Maximum file size that is allowed to be downloaded while processing links in MB                  |

By default, files are saved to a directory under this container. Save path can be changed by setting the `UPLOAD_PATH` environment variable. It is advised to mount an additional volume for the files saved by Text Extractor. Files are persisted as a point in time reference to the data that is embedded and ultimately ingested into the vector database.

## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**


### Running the microservice via Python (Option 1)

To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml --extra cpu
source impl/microservice/.venv/bin/activate
```

Then start the microservice:

```bash
python opea_text_extractor_microservice.py
```

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/text_extractor:latest -f comps/text_extractor/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="text_extractor" --env-file comps/text_extractor/impl/microservice/.env -p 9398:9398 opea/text_extractor:latest
```

### Example input

Text Extractor microservice as an input accepts a json containing links or files encoded in base64. Example requests can be found in followings paragraphs. It is possible to post both files and a list of link in one request.

#### File(s) Text Extractor

Files have to be encoded into Base64. This cURL format allows sending more data than using `-d`.

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:9398/v1/text_extractor <<JSON_DATA
{
  "files": [
    {
      "filename": "ia_spec.pdf",
      "data64": "$(base64 -w 0 ia_spec.pdf)"
    }
  ]
}
JSON_DATA
```

#### Link(s) Text Extractor

```bash
curl http://localhost:9398/v1/text_extractor \
  -X POST -H 'Content-Type: application/json' \
  -d '{ "links": ["https://example.com/"] }'
```

### Example output

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
