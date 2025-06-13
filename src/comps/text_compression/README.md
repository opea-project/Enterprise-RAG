# Text Compression Microservice

This microservice is designed to compressed text from loaded documents. Result of this microservice can then be passed to Text Splitter microservice and, later, to Embedding microservice and ultimately persisted in the system.

## Support Matrix

The microservice supports following compression techniques:

| Name | Class                                                                 |
|----------------|------------------------------------------------------------------|
| header_footer_stripper  | [HeaderFooterStripper](./utils/compressors/header_footer_stripper_compressor.py)              |
| ranking_aware_deduplication   | [RankedDeduplicator](./utils/compressors/ranking_aware_deduplication.py)              |


## Configuration options

Configuration is currently done via environment variables.

| Environment Variable             | Default Value             | Description                                                                                      |
|----------------------------------|---------------------------|--------------------------------------------------------------------------------------------------|
| `DEFAULT_TEXT_COMPRESSION_METHODS`   | `None`                    |  Default text compression methods to be used              |
| `OPEA_LOGGER_LEVEL`              | `INFO`                    | Microservice logging output level                                                                |
| `TEXT_COMPRESSION_USVC_PORT`             | `9397`                    | (Optional) Text Compression microservice port                                                            |

## Getting started

This microservice requires access to external network services for example for downloading models for text compression.

We offer 2 ways to run this microservice:
  - [via Python](#running-the-microservice-via-python-option-1)
  - [via Docker](#running-the-microservice-via-docker-option-2) **(recommended)**


### Running the microservice via Python (Option 1)

To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

Then start the microservice:

```bash
python opea_text_compression_microservice.py
```

### Running the microservice via Docker (Option 2)

Using a container is a preferred way to run the microservice.

#### Build the docker service

Navigate to the `src` directory and use the docker build command to create the image:

```bash
cd ../.. # src/ directory
docker build -t opea/text_compression:latest -f comps/text_compression/impl/microservice/Dockerfile .
```

#### Run the docker container

Remember, you can pass configuration variables by passing them via `-e` option into docker run command.

```bash
docker run -d --name="text_compression" --env-file comps/text_compression/impl/microservice/.env -p 9397:9397 opea/text_compression:latest
```

### Example input

```bash
curl -X POST -H "Content-Type: application/json"  http://localhost:9397/v1/text_compression  \
     -d '{"loaded_docs":[{"text":"1.3 \nGuiding Principles ......................................................................................................................... 8 \n1.3.1 \nAlignment to culture .................................................................................................. 8 \n1.3.2 \nCommunity Core Values \n...................................................................................................... 10 \n1.3.3","metadata":{"url":"https://example.com/","filename":"index.html","timestamp":1748520579.4694135}}], "compression_techniques": [{"name": "header_footer_stripper"}, {"name": "ranking_aware_deduplication"}]}'
```

### Example output

```json
{
  "id":"f606b14ff76191226ff516a4790bd7fb",
  "loaded_docs":[
    {
      "downstream_black_list":[],
      "id":"fe0fb12add60b0e6cfb4ee339397a530",
      "text":"1.3 \nGuiding Principles  8 \n1.3.1 \nAlignment to culture  8 \n1.3.2 \nCommunity Core Values \n 10 \n1.3.3",
      "metadata":{
        "url":"https://example.com/",
        "filename":"index.html",
        "timestamp":1748520579.4694135,
        "compression_technique":"header_footer_stripper, ranking_aware_deduplication",
        "original_length":421,
        "compressed_length":100,
        "compression_ratio":0.2375296912114014
      },
      "conversation_history":null
    }
  ],
  "chunk_size":null,
  "chunk_overlap":null,
  "use_semantic_chunking":false,
  "semantic_chunk_params":null
}
```
