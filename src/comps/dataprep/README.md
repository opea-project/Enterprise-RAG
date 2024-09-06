# OPEA Dataprep Microservice

This microservice is designed to extract text from data sent for processing. That data can be sent in form of files and/or links for scraping and further extraction. Result of this microservice can then be passed to embedding microservice and ultimately persisted in the system.

## Getting started

This microservice requires access to external network services for example for downloading models for parsing specific file formats for text extraction.

### Prerequisites
If running locally, install python requirements:

```bash
pip install -r impl/requirements.txt
```

### Running the Retriever Microservice

Example `docker-compose.yml`:
```
services:
  dataprep:
    build:
      context: .
      dockerfile: dataprep/impl/microservice/Dockerfile
      args: *proxy_args
    container_name: dataprep
    ports:
      - "9399:9399"
    environment: *proxy_args
```

To run this docker compose file, simply type:
`docker compose build && docker compose up -d`

Other configuration environment variables for this service:
- `CHUNK_SIZE` - (default: `1500`) - size of chunks that the data is split into for futher processing
- `CHUNK_OVERLAP` - (default: `100`) - size of chunks overlapping
- `PROCESS_TABLE` - (default: `true`) - choose if dataprep should process tables in PDF files
- `PROCESS_TABLE_STRATEGY` - (default: `fast`) - choose the table processing strategy
- `UPLOAD_PATH` - (default: `/tmp/opea_upload`) - path to where the data is saved

By default, files are saved to a directory under this container. Save path can be changed by setting the `UPLOAD_PATH` environment variable. It is advised to mount an additional volume for the files saved by dataprep. Files are persisted as a point in time reference to the data that is embedded and ultimately ingested into the vector database. 

### Example input

Dataprep microservice as an input accepts a json containing links or files as form data. Example requests can be found below:

#### File upload
```bash
  curl http://localhost:9399/v1/dataprep \
    -X POST -H "Content-Type: multipart/form-data" \
    -F "files=@./dataprep2/test/example.txt"
```

#### Link upload
```bash
  curl http://localhost:9399/v1/dataprep \
    -X POST -H 'Content-Type: application/json'
    -d '{"link_list": ['https://intel.com']}'
```

### Example output

```json
[
  {
    "id": "9aae0029b55498ed9951315e76ef3f5f",
    "text": "Intel AVX-512 is an instruction set [...]",
    "metadata": {
      "path": "/tmp/opea_upload/example.txt",
      "timestamp": 1724050405.923987
    }
  }
]
```
