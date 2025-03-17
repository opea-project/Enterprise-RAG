# LLM Guard Dataprep Guardrail Microservice
This microservice implements [LLM Guard](https://llm-guard.com/) (version: 0.3.14) Dataprep Scanners as part of the pipeline. The goal is to enable Secure AI and privacy-related capabilities for Enterprise RAG. Dataprep scanners scan the incoming documents for dataprep pipeline before they are passed to vector database and inform the user whether they are valid. LLM Guard Dataprep Guardrail Microservice enables all scanners provided by LLM Guard:
 - [BanCode](https://llm-guard.com/input_scanners/ban_code/)
 - [BanCompetitors](https://llm-guard.com/input_scanners/ban_competitors/)
 - [BanSubstrings](https://llm-guard.com/input_scanners/ban_substrings/)
 - [BanTopics](https://llm-guard.com/input_scanners/ban_topics/)
 - [Code](https://llm-guard.com/input_scanners/code/)
 - [Gibberish](https://llm-guard.com/input_scanners/gibberish/)
 - [InvisibleText](https://llm-guard.com/input_scanners/invisible_text/)
 - [Language](https://llm-guard.com/input_scanners/language/)
 - [PromptInjection](https://llm-guard.com/input_scanners/prompt_injection/)
 - [Regex](https://llm-guard.com/input_scanners/regex/)
 - [Secrets](https://llm-guard.com/input_scanners/secrets/)
 - [Sentiment](https://llm-guard.com/input_scanners/sentiment/)
 - [TokenLimit](https://llm-guard.com/input_scanners/token_limit/)
 - [Toxicity](https://llm-guard.com/input_scanners/toxicity/)

A detailed description of each scanner is available on [LLM Guard](https://llm-guard.com/).

## Configuration Options
The scanners can be configured only via environmental variables. All scanners can be configured via environmental variables for the microservice. They can be enabled during deployment or via configmap.

### Configuration via environmental variables
The LLM Guard Dataprep Guardrail Microservice configuration is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or exporting environmental variables as parameters to the container/pod. Each scanner can be configured in the .env file. Enabled scanners are executed sequentially. The environmental variables that are required for default run of particular scanner have values provided in .env file. Without providing them scanner will not work. The variables that do not have any values are optional, and without providing any values default values will be passed to scanner constructor. BanSubstrings scanner is enabled by default.

### BanCode scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCode scanner](https://llm-guard.com/input_scanners/ban_code/)
| Environment Variable       | Description                                                | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_CODE_ENABLED`         | Enables BanCode scanner.                                   | bool   | false               | Required            |
| `BAN_CODE_USE_ONNX`        | Enables usage of ONNX optimized model for BanCode scanner. | bool   | true                | Required            |
| `BAN_CODE_MODEL`           | Model to be used for BanCode scanner.                      | string | "MODEL_SM"            | Optional            |
| `BAN_CODE_THRESHOLD`       | Threshold for BanCode scanner.                             | float  | 0.97                  | Optional            |

### BanCompetitors scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCompetitors scanner](https://llm-guard.com/input_scanners/ban_competitors/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_COMPETITORS_ENABLED`  | Enables BanCompetitors scanner.                                               | bool   | false               | Required            |
| `BAN_COMPETITORS_USE_ONNX` | Enables usage of ONNX optimized model for BanCompetitors scanner.             | bool   | true                | Required            |
| `BAN_COMPETITORS_COMPETITORS` | List of competitors to be banned.                                          | string | "Competitor1,Competitor2,Competitor3" | Required |
| `BAN_COMPETITORS_THRESHOLD`| Threshold for BanCompetitors scanner.                                         | float  | 0.5                   | Optional            |
| `BAN_COMPETITORS_REDACT`   | Enables redaction of banned competitors.                                      | bool   | true                | Optional            |
| `BAN_COMPETITORS_MODEL`    | Model to be used for BanCompetitors scanner.                                  | string | "MODEL_V1"            | Optional            |

### BanSubstrings scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanSubstrings scanner](https://llm-guard.com/input_scanners/ban_substrings/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_SUBSTRINGS_ENABLED`   | Enables BanSubstrings scanner.                                                | bool   | false               | Required            |
| `BAN_SUBSTRINGS_SUBSTRINGS`| List of substrings to be banned.                                              | string | "backdoor,malware,virus"| Required            |
| `BAN_SUBSTRINGS_MATCH_TYPE`| Match type for substrings.                                                    | string | "str"                 | Optional            |
| `BAN_SUBSTRINGS_CASE_SENSITIVE` | Enables case sensitivity for detecting substrings.                       | bool   | false               | Optional            |
| `BAN_SUBSTRINGS_REDACT`    | Enables redaction of banned substrings.                                       | bool   | false               | Optional            |
| `BAN_SUBSTRINGS_CONTAINS_ALL` | Requires all substrings to be present.                                     | bool   | false               | Optional            |

### BanTopics scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanTopics scanner](https://llm-guard.com/input_scanners/ban_topics/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_TOPICS_ENABLED`       | Enables BanTopics scanner.                                   | bool   | false               | Required            |
| `BAN_TOPICS_USE_ONNX`      | Enables usage of ONNX optimized model for BanTopics scanner. | bool   | true                | Required            |
| `BAN_TOPICS_TOPICS`        | List of topics to be banned.                                 | string | "violence,attack,war" | Required            |
| `BAN_TOPICS_THRESHOLD`     | Threshold for BanTopics scanner.                             | float  | 0.5                   | Optional            |
| `BAN_TOPICS_MODEL`         | Model to be used for BanTopics scanner.                      | string | "MODEL_V1"            | Optional            |

### Code scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Code scanner](https://llm-guard.com/input_scanners/code/)
| Environment Variable       | Description                                                 | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------|--------|-----------------------|---------------------|
| `CODE_ENABLED`             | Enables Code scanner.                                       | bool   | false               | Required            |
| `CODE_USE_ONNX`            | Enables usage of ONNX optimized model for Code scanner.     | bool   | true                | Required            |
| `CODE_LANGUAGES`           | List of programming languages to be detected.               | string | "Java,Python"         | Required            |
| `CODE_MODEL`               | Model to be used for Code scanner.                          | string | "DEFAULT_MODEL"       | Optional            |
| `CODE_IS_BLOCKED`          | Enables blocking of detected code.                          | bool   | false               | Optional            |
| `CODE_THRESHOLD`           | Threshold for Code scanner.                                 | float  | 0.5                   | Optional            |

### Gibberish scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Gibberish scanner](https://llm-guard.com/input_scanners/gibberish/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `GIBBERISH_ENABLED`        | Enables Gibberish scanner.                                   | bool   | false               | Required            |
| `GIBBERISH_USE_ONNX`       | Enables usage of ONNX optimized model for Gibberish scanner. | bool   | true                | Required            |
| `GIBBERISH_MODEL`          | Model to be used for Gibberish scanner.                      | string | "DEFAULT_MODEL"       | Optional            |
| `GIBBERISH_THRESHOLD`      | Threshold for Gibberish scanner.                             | float  | 0.5                   | Optional            |
| `GIBBERISH_MATCH_TYPE`     | Whether to match the full text or individual sentences.      | string | "full"                | Optional            |

### InvisibleText scanner
Detailed description of the scanner can be found in [LLM Guard documentation for InvisibleText scanner](https://llm-guard.com/input_scanners/invisible_text/)
| Environment Variable       | Description                    | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------|--------|-----------------------|---------------------|
| `INVISIBLE_TEXT_ENABLED`   | Enables InvisibleText scanner. | bool   | false               | Required            |

### Language scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Language scanner](https://llm-guard.com/input_scanners/language/)
| Environment Variable                | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `LANGUAGE_ENABLED`                  | Enables Language scanner.                                    | bool   | false               | Required            |
| `LANGUAGE_USE_ONNX`                 | Enables usage of ONNX optimized model for Language scanner.  | bool   | true                | Required            |
| `LANGUAGE_VALID_LANGUAGES`          | List of supported languages for the Language scanner.        | string | "en,es"               | required            |
| `LANGUAGE_MODEL`                    | Model to be used for Language scanner.                       | string | "DEFAULT_MODEL"       | Optional            |
| `LANGUAGE_THRESHOLD`                | Threshold for Language scanner.                              | float  | 0.6                   | Optional            |
| `LANGUAGE_MATCH_TYPE`               | Match type for language detection (e.g., full, partial).     | string | "full"                | Optional            |

### PromptInjection scanner
Detailed description of the scanner can be found in [LLM Guard documentation for PromptInjection scanner](https://llm-guard.com/input_scanners/prompt_injection/)
| Environment Variable          | Description                                                        | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------|--------------------------------------------------------------------|--------|-----------------------|---------------------|
| `PROMPT_INJECTION_ENABLED`    | Enables PromptInjection scanner.                                   | bool   | false               | Required            |
| `PROMPT_INJECTION_USE_ONNX`   | Enables usage of ONNX optimized model for PromptInjection scanner. | bool   | true                | Required            |
| `PROMPT_INJECTION_MODEL`      | Model to be used for PromptInjection scanner.                      | string | "V1_MODEL"            | Optional            |
| `PROMPT_INJECTION_THRESHOLD`  | Threshold for PromptInjection scanner.                             | float  | 0.92                  | Optional            |
| `PROMPT_INJECTION_MATCH_TYPE` | Match type for prompt injection detection.                         | string | "full"                | Optional            |


### Regex scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Regex scanner](https://llm-guard.com/input_scanners/regex/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `REGEX_ENABLED`            | Enables Regex scanner.                                                        | bool   | false               | Required            |
| `REGEX_PATTERNS`           | List of regex patterns to be used.                                            | string | "Bearer [A-Za-z0-9-._~+/]+"| Required            |
| `REGEX_IS_BLOCKED`         | Enables blocking of matched patterns.                                         | bool   | true               | Optional            |
| `REGEX_MATCH_TYPE`         | Match type for regex patterns (e.g., full, partial).                          | string | "SEARCH"              | Optional            |
| `REGEX_REDACT`             | Enables redaction of output.                                                  | bool   | false               | Optional            |

### Secrets scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Secrets scanner](https://llm-guard.com/input_scanners/secrets/)
| Environment Variable       | Description                                                                   |
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SECRETS_ENABLED`          | Enables Secrets scanner.                                                      | bool   | false               | Required            |
| `SECRETS_REDACT_MODE`      | Redaction mode for detected secrets.                                          | string | "REDACT_ALL"          | Optional            |

### Sentiment scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Sentiment scanner](https://llm-guard.com/input_scanners/sentiment/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SENTIMENT_ENABLED`        | Enables Sentiment scanner.                                                    | bool   | false               | Required            |
| `SENTIMENT_THRESHOLD`      | Threshold for Sentiment scanner.                                              | float  | 0.3                   | Optional            |
| `SENTIMENT_LEXICON`        | Lexicon to be used for sentiment analysis.                                    | string | "vader_lexicon"       | Optional            |

### TokenLimit scanner
Detailed description of the scanner can be found in [LLM Guard documentation for TokenLimit scanner](https://llm-guard.com/input_scanners/token_limit/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `TOKEN_LIMIT_ENABLED`      | Enables TokenLimit scanner.                                                   | bool   | false               | Required            |
| `TOKEN_LIMIT_LIMIT`        | Threshold for TokenLimit scanner. Default: 1000.                              | int    | 4096                  | Required            |
| `TOKEN_LIMIT_ENCODING_NAME`| Encoding name for TokenLimit scanner.                                         | string | "cl100k_base"         | Optional            |
| `TOKEN_LIMIT_MODEL_NAME`   | Model name to be used for TokenLimit scanner.                                 | string | no value              | Optional            |

### Toxicity scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Toxicity scanner](https://llm-guard.com/input_scanners/toxicity/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `TOXICITY_ENABLED`         | Enables Toxicity scanner.                                                     | bool   | false               | Required            |
| `TOXICITY_USE_ONNX`        | Enables usage of ONNX optimized model for Toxicity scanner.                   | bool   | true                | Required            |
| `TOXICITY_MODEL`           | Model to be used for Toxicity scanner.                                        | string | "DEFAULT_MODEL"       | Optional            |
| `TOXICITY_THRESHOLD`       | Threshold for Toxicity scanner.                                               | float  | 0.5                   | Optional            |
| `TOXICITY_MATCH_TYPE`      | Match type for toxicity detection.                                            | string | "full"                | Optional            |

## Getting started

### Prerequisite

1. **Navigate to the microservice directory**:
    ```sh
    cd src/comps/guardrails/llm_guard_dataprep_guardrail
    ```

2. **Set up the environment variables**:
    - Edit the `.env` file to configure the necessary environment variables for the scanners you want to enable.

### 🚀1. Start LLM Guard Dataprep Guardrail Microservice with Python (Option 1)

To start the LLM Guard Dataprep Guardrail microservice, you need to install python packages first.

#### 1.1. Install Requirements
To freeze the dependencies of a particular microservice, we utilize [uv](https://github.com/astral-sh/uv) project manager. So before installing the dependencies, installing uv is required.
Next, use `uv sync` to install the dependencies. This command will create a virtual environment.

```bash
pip install uv
uv sync --locked --no-cache --project impl/microservice/pyproject.toml
source impl/microservice/.venv/bin/activate
```

#### 1.2. Start Microservice

```bash
python opea_llm_guard_dataprep_guardrail_microservice.py
```

### 🚀2. Start LLM Guard Dataprept Guardrail Microservice with Docker (Option 2)

#### 2.1. Build the Docker image:
```sh
cd ../../.. # src/ directory
docker build -t opea/in-guard:latest -f comps/guardrails/llm_guard_dataprep_guardrail/impl/microservice/Dockerfile .
```

#### 2.2. Run the Docker container, for example:
```sh
docker run -d -e BAN_SUBSTRINGS_EMABLED=true -p 8070:8070 opea/dpguard:latest
```

### 3. Verify the LLM Guard Dataprep Guardrail Microservice

#### 3.1. Check Status

```bash
curl http://localhost:8070/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

####  3.2. Sending a Request

The dataprep guardrail microservice accepts input as multiple documents containing text. Below are examples of how to structure the reques

**Example Input**

For multiple documents:
```bash
curl http://localhost:8070/v1/llmguarddataprep \
  -X POST \
  -d '{"docs": [{"text":"Hello, world!"}, {"text":"Hello, world!"}]}' \
  -H 'Content-Type: application/json'
```

**Example Output**

The output of an dataprep guardrail microservice is a JSON object that includes the scanned texts or 466 error code.

```json
{
  "docs": [
    {
      "text": "content chunk 1",
    },
    {
      "text": "content chunk 2",

    },
    {
      "text": "content chunk 3",
    }
  ]
}
```
