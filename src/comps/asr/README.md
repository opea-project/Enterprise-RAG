# ASR Microservice

The ASR Microservice is designed to efficiently convert audio input into textual transcriptions, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality transcriptions that capture the spoken content accurately, making it ideal for applications in natural language processing, voice assistants, and similar fields.

**Key Features**

- **High Performance**: Optimized for quick and reliable conversion of audio data into text transcriptions.
- **Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.
- **Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.
- **Customizable**: Supports configuration and customization to meet specific use case requirements, including different ASR models and preprocessing techniques.

Users are able to configure and build ASR-related services according to their actual needs.

## Support matrix

Support for specific model servers with Dockerfiles or build instruction.

| Model server                | langchain | llama_index |
| ------------                | ----------| ------------|
| [torchserve](./impl/model-server/torchserve)  | &#x2713;  | &#x2717;    |

## Configuration Options

The configuration for the ASR Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or by exporting environment variables.

| Environment Variable            | Description                                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `ASR_USVC_PORT`                 | The port of the microservice, by default 8300.                                                                        |
| `ASR_MODEL_NAME`                | The name of ASR model to be used (e.g., "openai/whisper-small")                                                          |
| `ASR_MODEL_SERVER`              | Specifies the type of model server (e.g. "torchserve")                                                               |
| `ASR_MODEL_SERVER_ENDPOINT`     | URL of the model server endpoint, e.g., "http://localhost:8090"                                                       |


## Getting started

### Prerequisite: Start ASR Model Server

The ASR Microservice interacts with an ASR model endpoint, which must be operational and accessible at the URL specified by the `ASR_MODEL_SERVER_ENDPOINT` env.

Depending on the model server you want to use, follow the appropriate instructions in the [impl/model_server](impl/model_server/) directory to set up and start the service. 


Currently, we provide these ways to implement a model server for ASR:

1. Utilize [**_Torchserve_**](./impl/model-server/torchserve/), which supports [Intel® Extension for PyTorch*](https://github.com/intel/intel-extension-for-pytorch) for a performance boost on Intel-based Hardware.

Refer to `README.md` of a particular library to get more information on starting a model server.


## 🚀1. Start ASR Microservice with Python (Option 1)

To start the ASR microservice, you need to install requirements first.

#### 1.1. Install Requirements
First, install essential requirements for the microservice:

```bash
# common
pip install -r impl/microservice/requirements.txt
```

#### 1.2. Start Microservice

```bash
python asr_microservice.py
```

### 🚀2. Start ASR Microservice with Docker (Option 2)

#### 2.1. Build the Docker Image:
Navigate to the `src` directory and use the docker build command to create the image:
```bash

cd comps/asr/impl/model-server/torchserve/docker

docker compose --env-file=.env up --build -d

```
Please note that the building process may take a while to complete.

#### 2.2. Run the Docker Container:

Ensure that the `ASR_MODEL_SERVER` corresponds to the specific image built with the relevant requirements:

```bash

```

If the model server is running at a different endpoint than the default, update the `ASR_MODEL_SERVER_ENDPOINT` variable accordingly. Here's an example of how to pass configuration using the docker run command:



### 3. Verify the ASR Microservice

#### 3.1. Check Status

```bash
curl http://localhost:8300/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The ASR microservice accepts input as either a single audio file or multiple audio files. Below are examples of how to structure the request.

**Example Input**

 For a single audio input:
  ```bash
  curl http://localhost:8300/v1/audio/transcriptions \
      -H "Content-Type: multipart/form-data"      \
      -F "data=@audiopath"
  ```


**Example Output**

The output of an ASR microservice is a JSON object that includes the input audio, the computed transcriptions, and additional parameters.

For a audio input:
```json
[
  "discuss the evolution of text to speech tts technology from its early beginnings to the present day unlike the advancements in natural language processing that have contributed to more realistic and human like speech synthesis also explore the various applications of tts in education accessibility and customer service and predict future trends in this field write a comprehensive overview of text to speech tts technology"
]
```



## Additional Information
### Project Structure

The project is organized into several directories:
- `impl/`: This directory contains the implementation. It includes the microservice folder with the Dockerfile for the microservice, and the `model_server` directory, which provides setup and running instructions for various model servers, such as TEI or OVMS.
- `utils/`: This directory contains utility scripts and modules that are used by the ASR Microservice.

The tree view of the main directories and files:

```bash
  .
  ├── impl/
  │   ├── microservice/
  │   │   ├── .env
  │   │   ├── Dockerfile
  │   │   └── requirements.txt
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
  │   ├── asr_utils.py
  │   ├── api_config/
  │   └── api_config.yml
  │   
  ├── README.md
  └── asr_microservice.py
```

#### Tests
- `src/tests/unit/asr/`: Contains unit tests for the ASR Microservice components
