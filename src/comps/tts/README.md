# Text-to-Speech (TTS) Microservice

The TTS Microservice is designed to efficiently convert textual strings into speech audio, facilitating seamless integration into various applications requiring text-to-speech capabilities. This service utilizes advanced algorithms to generate high-quality speech that captures the natural essence of the input text, making it ideal for applications in accessibility, virtual assistants, and similar fields.

**Key Features**

- **High Performance**: Optimized for quick and reliable conversion of textual data into speech audio.
- **Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.
- **Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.
- **Customizable**: Supports configuration and customization to meet specific use case requirements, including different TTS models and preprocessing techniques.

Users are able to configure and build TTS-related services according to their actual needs.

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server                | microsoft/speecht5_tts |
| ------------                | ---------------------- |
| [torchserve](./impl/model-server/torchserve)  | &#x2713;  |

## Configuration Options

The configuration for the TTS Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `TTS_USVC_PORT`                 | The port of the microservice, by default 7000.                                                                        |
| `TTS_MODEL_NAME`                | The name of TTS model to be used (e.g., "microsoft/speecht5_tts")                                             |
| `TTS_CONNECTOR`                 | The framework used to connect to the model. Supported value: 'microsoft' |
| `TTS_MODEL_SERVER`              | Specifies the type of model server (e.g. "torchserve")                                                               |
| `TTS_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint, e.g., "http://localhost:8090"                                                       |


## Getting started

### Prerequisite: Start TTS Model Server

The TTS Microservice interacts with a TTS model endpoint, which must be operational and accessible at the URL specified by the `TTS_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the appropriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. 

Currently, we provide these ways to implement a model server for TTS:

1. Utilize [**_Torchserve_**](./impl/model-server/torchserve/), which supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

Refer to `README.md` of a particular library to get more information on starting a model server.


## 🚀1. Start TTS Microservice with Python (Option 1)

To start the TTS microservice, you need to install requirements first.

#### 1.1. Install Requirements
First, install essential requirements for the microservice:

```bash
# common
pip install -r impl/microservice/requirements.txt
```

Next, install specific model server requirements:

```bash
# for microsoft
pip install -r impl/microservice/requirements/microsoft.txt
```

#### 1.2. Start Microservice

```bash
python opea_tts_microservice.py
```

### 🚀2. Start TTS Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash
cd ../../

# for microsoft
docker build --target microsoft -t opea/tts:microsoft -f comps/tts/impl/microservice/Dockerfile .
```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:

Ensure that the `TTS_CONNECTOR` corresponds to the specific image built with the relevant requirements. Below is an example for Microsoft:

```bash
# for microsoft
docker run -d --name="tts-microservice" \
  -e TTS_CONNECTOR=microsoft \
  --net=host \
  --ipc=host \
  opea/tts:microsoft
```

If the model server is running at a different endpoint than the default, update the `TTS_MODEL_SERVER_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:

```bash
# for microsoft
docker run -d --name="tts-microservice" \
  -e TTS_MODEL_SERVER_ENDPOINT="http://localhost:8090" \
  -e TTS_MODEL_NAME="microsoft/speecht5_tts" \
  -e TTS_CONNECTOR="microsoft" \
  -e TTS_MODEL_SERVER="torchserve" \
  --net=host \
  --ipc=host \
  opea/tts:microsoft
```


### 3. Verify the TTS Microservice

#### 3.1. Check Status

```bash
curl http://localhost:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The TTS microservice accepts input as either a single text string or multiple documents containing text. Below are examples of how to structure the request.

**Example Input**

 For a single text input:
  ```bash
  curl http://localhost:7000/v1/tts \
    -X POST \
    -d '{"text":"Hello, world!"}' \
    -H 'Content-Type: application/json'
  ```

For multiple documents:
```bash
curl http://localhost:7000/v1/tts \
  -X POST \
  -d '{"docs": [{"text":"Hello, world!"}, {"text":"Hello, world!"}]}' \
  -H 'Content-Type: application/json'
```

**Example Output**

The output of a TTS microservice is a JSON object that includes the input text, the computed speech audio, and additional parameters.

For a single text input:
```json
{
  "id":"d4e67d3c7353b13c3821d241985705b1",
  "text":"Hello, world!",
  "audio":"<base64_encoded_audio>",
  "metadata": {}
}
```

For multiple documents:
```json
{
  "id":"d4e67d3c7353b13c3821d241985705b1",
  "docs": [
    {
      "id": "27ff622c495813be476c892bb6940bc5",
      "text":"Hello, world!",
      "audio":"<base64_encoded_audio>",
      "metadata": {}
    },
    {
      "id": "937f9b71a2fa0e6437e33c55bec8e1ea",
      "text": "Hello, world!",
      "audio":"<base64_encoded_audio>",
      "metadata": {}
    }
  ]
}
```


## Additional Information
### Project Structure

The project is organized into several directories:
- `impl/`: This directory contains the implementation. It includes the microservice folder with the Dockerfile for the microservice, and the `model_server` directory, which provides setup and running instructions for various model servers, such as Torchserve.
- `utils/`: This directory contains utility scripts and modules that are used by the TTS Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── .env
  │   │   ├── Dockerfile
  │   │   └── requirements.txt
  │   │   └── requirements/
  │   │      ├── microsoft.txt
  │   │
  │   ├── model_server/
  │   │   ├── torchserve/
  │   │   │   ├── README.md
  │   │   │   ├── run_torchserve.sh
  │   │   │   └── docker/
  │   │   │       ├── .env
  │   │   │       └── docker-compose.yml
  │   │   │  
  │   │   └── ...
  │   └── ...
  │
  ├── utils/
  │   ├── opea_tts.py
  │   ├── api_config/
  │   │   └── api_config.yml
  │   │
  │   └── wrappers/
  │       ├── wrapper.py
  │       ├── wrapper_microsoft.py
  │   
  ├── README.md
  └── opea_tts_microservice.py
```

#### Tests
- `src/tests/unit/tts/`: Contains unit tests for the TTS Microservice components

