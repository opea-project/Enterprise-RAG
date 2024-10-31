# Dataprep Microservice

This microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

## Support Matrix

Supported files that dataprep can extract data from:

| File Extension | Loader Class                                                                 |
|----------------|------------------------------------------------------------------------------|
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

## Configuration options

Configuration is currently done via environment variables.

| Environment Variable    | Default Value     | Description                                                                                      |
|-------------------------|-------------------|--------------------------------------------------------------------------------------------------|
| `CHUNK_SIZE`            | `1500`            | Size of chunks that the data is split into for further processing                                |
| `CHUNK_OVERLAP`         | `100`             | Size of chunks overlapping                                                                       |
| `PROCESS_TABLE`         | `true`            | Choose if dataprep should process tables in PDF files                                            |
| `PROCESS_TABLE_STRATEGY`| `fast`            | Choose the table processing strategy                                                             |
| `UPLOAD_PATH`           | `/tmp/opea_upload`| Path to where the data is saved                                                                  |

By default, files are saved to a directory under this container. Save path can be changed by setting the `UPLOAD_PATH` environment variable. It is advised to mount an additional volume for the files saved by dataprep. Files are persisted as a point in time reference to the data that is embedded and ultimately ingested into the vector database. 


## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

We offer 2 ways to run this microservice: 
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**


### Running the microservice via Python (Option 1)

If running locally, install python requirements:

```bash
pip install -r impl/microservice/requirements.txt
```

Then start the microservice:

```bash
python opea_dataprep_microservice.py
```

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/dataprep:latest -f comps/dataprep/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="dataprep" --env-file comps/dataprep/impl/microservice/.env -p 9399:9399 opea/dataprep:latest
```

### Example input

Dataprep microservice as an input accepts a json containing links or files encoded in base64. Example requests can be found in followings paragraphs. It is possible to post both files and a list of link in one request.

#### File(s) dataprep

Files have to be encoded into Base64. This cURL format allows sending more data than using `-d`.

```bash
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:9399/v1/dataprep <<JSON_DATA
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

#### Link(s) dataprep

```bash
curl http://localhost:9399/v1/dataprep \
  -X POST -H 'Content-Type: application/json' \
  -d '{ "links": ["https://intel.com"] }'
```

### Example output

For both files and links the output has the same format, containg the extracted text array. Text is chunked depenting on `CHUNK_SIZE` and `CHUNK_OVERLAP` parameters. The following example response shows how a file is chunked:

```json
{
  "docs": [
    {
      "text": "content chunk 1",
      "metadata": {
        "path": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    },
    {
      "text": "content chunk 2",
      "metadata": {
        "path": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    },
    {
      "text": "content chunk 3",
      "metadata": {
        "path": "/tmp/opea_upload/test.txt",
        "timestamp": 1726226461.738807
      }
    }
  ]
}
```

## Additional Information
   
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains the implementation of the supported dataprep service.

- `utils/`: This directory contains utility scripts and modules that are used by the Dataprep Microservice. It included the web crawler and script for extracting text from various files.

The tree view of the main directories and files:

```bash
  .
  ├── impl
  │   └── microservice
  │       ├── Dockerfile
  │       └── requirements.txt
  |       └── .env
  ├── opea_dataprep_microservice.py
  ├── README.md
  ├── test
  │   ├── file2.txt
  │   ├── file.txt
  │   ├── ia.pdf
  │   ├── ia_spec.pdf
  │   └── test_data.pdf
  └── utils
      ├── crawler.py
      ├── file_loaders
      │   ├── abstract_loader.py
      │   ├── load_csv.py
      │   ├── load_doc.py
      │   ├── load_html.py
      │   ├── load_image.py
      │   ├── load_json.py
      │   ├── load_md.py
      │   ├── load_pdf.py
      │   ├── load_ppt.py
      │   ├── load_txt.py
      │   ├── load_xls.py
      │   ├── load_xml.py
      │   └── load_yaml.py
      ├── file_parser.py
      ├── opea_dataprep.py
      ├── splitter.py
      └── utils.py
```
