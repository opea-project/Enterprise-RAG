# LLM Guard Input Guardrail Microservice
This microservice implements [LLM Guard](https://llm-guard.com/) (version: 0.3.14) Input Scanners as part of the pipeline. The goal is to enable Secure AI and privacy-related capabilities for Enterprise RAG. Input scanners scan the incoming prompt and context before they are passed to LLM and inform the user whether they are valid. LLM Guard Input Guardrail Microservice enables all scanners provided by LLM Guard:
 - [Anonymize](https://llm-guard.com/input_scanners/anonymize/)
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
The scanners can be configured in two places: via UI and via environmental variables. There are five scanners enabled in UI. All scanners can be configured via environmental variables for the microservice.

### Configuration via UI
Scanners currently configurable from UI, from Admin Panel:
 - [BanCompetitors](https://llm-guard.com/input_scanners/ban_competitors/)
 - [BanSubstrings](https://llm-guard.com/input_scanners/ban_substrings/)
 - [Gibberish](https://llm-guard.com/input_scanners/gibberish/)
 - [Language](https://llm-guard.com/input_scanners/language/)
 - [PromptInjection](https://llm-guard.com/input_scanners/prompt_injection/)

### Configuration via environmental variables
The LLM Guard Input Guardrail Microservice configuration is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or exporting environmental variables as parameters to the container/pod. Each scanner can be configured in the .env file. Enabled scanners are executed sequentially. The environmental variables that are required for default run of particular scanner have values provided in .env file. Without providing them scanner will not work. The variables that do not have any values are optional, and without providing any values default values will be passed to scanner constructor.

### Anonymize scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Anonymize scanner](https://llm-guard.com/input_scanners/anonymize/)
| Environment Variable       | Description                                                     | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-----------------------------------------------------------------|--------|-----------------------|---------------------|
| `ANONYMIZE_ENABLED`        | Enables Anonymize scanner.                                      | bool   | "false"               | Required            |
| `ANONYMIZE_USE_ONNX`       | Enables usage of ONNX optimized model for Anonymize scanner.    | bool   | "true"                | Required            |
| `ANONYMIZE_HIDDEN_NAMES`   | List of names to be anonymized e.g. [REDACTED_CUSTOM_1].        | string | no value              | Optional            |
| `ANONYMIZE_ALLOWED_NAMES`  | List of names allowed in the text without anonymizing.          | string | no value              | Optional            |
| `ANONYMIZE_ENTITY_TYPES`   | List of entity types to be detected.                            | string | no value              | Optional            |
| `ANONYMIZE_PREAMBLE`       | Text to be added before sanitized prompt.                       | string | no value              | Optional            |
| `ANONYMIZE_REGEX_PATTERNS` | Custom regex patterns for anonymization.                        | string | no value              | Optional            |
| `ANONYMIZE_USE_FAKER`      | Enables usage of Faker library for generating fake data.        | bool   | "false"               | Optional            |
| `ANONYMIZE_RECOGNIZER_CONF`| Configuration for entity recognizers.                           | string | no value              | Optional            |
| `ANONYMIZE_THRESHOLD`      | Acceptance threshold for anonymization.                         | float  | 0.5                   | Optional            |
| `ANONYMIZE_LANGUAGE`       | Language model to be used for anonymization.                    | string | "en"                  | Optional            |

### BanCode scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCode scanner](https://llm-guard.com/input_scanners/ban_code/)
| Environment Variable       | Description                                                | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_CODE_ENABLED`         | Enables BanCode scanner.                                   | bool   | "false"               | Required            |
| `BAN_CODE_USE_ONNX`        | Enables usage of ONNX optimized model for BanCode scanner. | bool   | "true"                | Required            |
| `BAN_CODE_MODEL`           | Model to be used for BanCode scanner.                      | string | "MODEL_SM"            | Optional            |
| `BAN_CODE_THRESHOLD`       | Threshold for BanCode scanner.                             | float  | 0.97                  | Optional            |

### BanCompetitors scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCompetitors scanner](https://llm-guard.com/input_scanners/ban_competitors/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_COMPETITORS_ENABLED`  | Enables BanCompetitors scanner.                                               | bool   | "false"               | Required            |
| `BAN_COMPETITORS_USE_ONNX` | Enables usage of ONNX optimized model for BanCompetitors scanner.             | bool   | "true"                | Required            |
| `BAN_COMPETITORS_COMPETITORS` | List of competitors to be banned.                                          | string | "Competitor1,Competitor2,Competitor3" | Required |
| `BAN_COMPETITORS_THRESHOLD`| Threshold for BanCompetitors scanner.                                         | float  | 0.5                   | Optional            |
| `BAN_COMPETITORS_REDACT`   | Enables redaction of banned competitors.                                      | bool   | "true"                | Optional            |
| `BAN_COMPETITORS_MODEL`    | Model to be used for BanCompetitors scanner.                                  | string | "MODEL_V1"            | Optional            |

### BanSubstrings scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanSubstrings scanner](https://llm-guard.com/input_scanners/ban_substrings/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_SUBSTRINGS_ENABLED`   | Enables BanSubstrings scanner.                                                | bool   | "false"               | Required            |
| `BAN_SUBSTRINGS_SUBSTRINGS`| List of substrings to be banned.                                              | string | "backdoor,malware,virus"| Required            |
| `BAN_SUBSTRINGS_MATCH_TYPE`| Match type for substrings.                                                    | string | "str"                 | Optional            |
| `BAN_SUBSTRINGS_CASE_SENSITIVE` | Enables case sensitivity for detecting substrings.                       | bool   | "false"               | Optional            |
| `BAN_SUBSTRINGS_REDACT`    | Enables redaction of banned substrings.                                       | bool   | "false"               | Optional            |
| `BAN_SUBSTRINGS_CONTAINS_ALL` | Requires all substrings to be present.                                     | bool   | "false"               | Optional            |

### BanTopics scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanTopics scanner](https://llm-guard.com/input_scanners/ban_topics/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_TOPICS_ENABLED`       | Enables BanTopics scanner.                                   | bool   | "false"               | Required            |
| `BAN_TOPICS_USE_ONNX`      | Enables usage of ONNX optimized model for BanTopics scanner. | bool   | "true"                | Required            |
| `BAN_TOPICS_TOPICS`        | List of topics to be banned.                                 | string | "violence,attack,war" | Required            |
| `BAN_TOPICS_THRESHOLD`     | Threshold for BanTopics scanner.                             | float  | 0.5                   | Optional            |
| `BAN_TOPICS_MODEL`         | Model to be used for BanTopics scanner.                      | string | "MODEL_V1"            | Optional            |

### Code scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Code scanner](https://llm-guard.com/input_scanners/code/)
| Environment Variable       | Description                                                 | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------|--------|-----------------------|---------------------|
| `CODE_ENABLED`             | Enables Code scanner.                                       | bool   | "false"               | Required            |
| `CODE_USE_ONNX`            | Enables usage of ONNX optimized model for Code scanner.     | bool   | "true"                | Required            |
| `CODE_LANGUAGES`           | List of programming languages to be detected.               | string | "Java,Python"         | Required            |
| `CODE_MODEL`               | Model to be used for Code scanner.                          | string | "DEFAULT_MODEL"       | Optional            |
| `CODE_IS_BLOCKED`          | Enables blocking of detected code.                          | bool   | "false"               | Optional            |
| `CODE_THRESHOLD`           | Threshold for Code scanner.                                 | float  | 0.5                   | Optional            |

### Gibberish scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Gibberish scanner](https://llm-guard.com/input_scanners/gibberish/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `GIBBERISH_ENABLED`        | Enables Gibberish scanner.                                   | bool   | "false"               | Required            |
| `GIBBERISH_USE_ONNX`       | Enables usage of ONNX optimized model for Gibberish scanner. | bool   | "true"                | Required            |
| `GIBBERISH_MODEL`          | Model to be used for Gibberish scanner.                      | string | "DEFAULT_MODEL"       | Optional            |
| `GIBBERISH_THRESHOLD`      | Threshold for Gibberish scanner.                             | float  | 0.5                   | Optional            |
| `GIBBERISH_MATCH_TYPE`     | Whether to match the full text or individual sentences.      | string | "full"                | Optional            |

### InvisibleText scanner
Detailed description of the scanner can be found in [LLM Guard documentation for InvisibleText scanner](https://llm-guard.com/input_scanners/invisible_text/)
| Environment Variable       | Description                    | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------|--------|-----------------------|---------------------|
| `INVISIBLE_TEXT_ENABLED`   | Enables InvisibleText scanner. | bool   | "false"               | Required            |

### Language scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Language scanner](https://llm-guard.com/input_scanners/language/)
| Environment Variable                | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `LANGUAGE_ENABLED`                  | Enables Language scanner.                                    | bool   | "false"               | Required            |
| `LANGUAGE_USE_ONNX`                 | Enables usage of ONNX optimized model for Language scanner.  | bool   | "true"                | Required            |
| `LANGUAGE_VALID_LANGUAGES`          | List of supported languages for the Language scanner.        | string | "en,es"               | required            |
| `LANGUAGE_MODEL`                    | Model to be used for Language scanner.                       | string | "DEFAULT_MODEL"       | Optional            |
| `LANGUAGE_THRESHOLD`                | Threshold for Language scanner.                              | float  | 0.6                   | Optional            |
| `LANGUAGE_MATCH_TYPE`               | Match type for language detection (e.g., full, partial).     | string | "full"                | Optional            |

### PromptInjection scanner
Detailed description of the scanner can be found in [LLM Guard documentation for PromptInjection scanner](https://llm-guard.com/input_scanners/prompt_injection/)
| Environment Variable          | Description                                                        | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------|--------------------------------------------------------------------|--------|-----------------------|---------------------|
| `PROMPT_INJECTION_ENABLED`    | Enables PromptInjection scanner.                                   | bool   | "false"               | Required            |
| `PROMPT_INJECTION_USE_ONNX`   | Enables usage of ONNX optimized model for PromptInjection scanner. | bool   | "true"                | Required            |
| `PROMPT_INJECTION_MODEL`      | Model to be used for PromptInjection scanner.                      | string | "V1_MODEL"            | Optional            |
| `PROMPT_INJECTION_THRESHOLD`  | Threshold for PromptInjection scanner.                             | float  | 0.92                  | Optional            |
| `PROMPT_INJECTION_MATCH_TYPE` | Match type for prompt injection detection.                         | string | "full"                | Optional            |


### Regex scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Regex scanner](https://llm-guard.com/input_scanners/regex/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `REGEX_ENABLED`            | Enables Regex scanner.                                                        | bool   | "false"               | Required            |
| `REGEX_PATTERNS`           | List of regex patterns to be used.                                            | string | "Bearer [A-Za-z0-9-._~+/]+"| Required            |
| `REGEX_IS_BLOCKED`         | Enables blocking of matched patterns.                                         | bool   | "true"               | Optional            |
| `REGEX_MATCH_TYPE`         | Match type for regex patterns (e.g., full, partial).                          | string | "SEARCH"              | Optional            |
| `REGEX_REDACT`             | Enables redaction of output.                                                  | bool   | "false"               | Optional            |

### Secrets scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Secrets scanner](https://llm-guard.com/input_scanners/secrets/)
| Environment Variable       | Description                                                                   |
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SECRETS_ENABLED`          | Enables Secrets scanner.                                                      | bool   | "false"               | Required            |
| `SECRETS_REDACT_MODE`      | Redaction mode for detected secrets.                                          | string | "REDACT_ALL"          | Optional            |

### Sentiment scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Sentiment scanner](https://llm-guard.com/input_scanners/sentiment/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SENTIMENT_ENABLED`        | Enables Sentiment scanner.                                                    | bool   | "false"               | Required            |
| `SENTIMENT_THRESHOLD`      | Threshold for Sentiment scanner.                                              | float  | 0.3                   | Optional            |
| `SENTIMENT_LEXICON`        | Lexicon to be used for sentiment analysis.                                    | string | "vader_lexicon"       | Optional            |

### TokenLimit scanner
Detailed description of the scanner can be found in [LLM Guard documentation for TokenLimit scanner](https://llm-guard.com/input_scanners/token_limit/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `TOKEN_LIMIT_ENABLED`      | Enables TokenLimit scanner.                                                   | bool   | "false"               | Required            |
| `TOKEN_LIMIT_LIMIT`        | Threshold for TokenLimit scanner. Default: 1000.                              | int    | 4096                  | Required            |
| `TOKEN_LIMIT_ENCODING_NAME`| Encoding name for TokenLimit scanner.                                         | string | "cl100k_base"         | Optional            |
| `TOKEN_LIMIT_MODEL_NAME`   | Model name to be used for TokenLimit scanner.                                 | string | no value              | Optional            |

### Toxicity scanner
Detailed description of the scanner can be found in [LLM Guard documentation for Toxicity scanner](https://llm-guard.com/input_scanners/toxicity/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `TOXICITY_ENABLED`         | Enables Toxicity scanner.                                                     | bool   | "false"               | Required            |
| `TOXICITY_USE_ONNX`        | Enables usage of ONNX optimized model for Toxicity scanner.                   | bool   | "true"                | Required            |
| `TOXICITY_MODEL`           | Model to be used for Toxicity scanner.                                        | string | "DEFAULT_MODEL"       | Optional            |
| `TOXICITY_THRESHOLD`       | Threshold for Toxicity scanner.                                               | float  | 0.5                   | Optional            |
| `TOXICITY_MATCH_TYPE`      | Match type for toxicity detection.                                            | string | "full"                | Optional            |

## Getting started

### Prerequisite

1. **Navigate to the microservice directory**:
    ```sh
    cd src/comps/guardrails/llm_guard_input_guardrail
    ```

2. **Set up the environment variables**:
    - Edit the `.env` file to configure the necessary environment variables for the scanners you want to enable.

### 🚀1. Start LLM Guard Input Guardrail Microservice with Python (Option 1)

To start the LLM Guard Intput Guardrail microservice, you need to install python packages first.

#### 1.1. Install Requirements

```bash
pip install -r impl/microservice/requirements.txt
```

#### 1.2. Start Microservice

```bash
python opea_llm_guard_input_guardrail_microservice.py
```

### 🚀2. Start LLM Guard Input Guardrail Microservice with Docker (Option 2)

#### 2.1. Build the Docker image:
```sh
cd ../../.. # src/ directory
docker build -t opea/in-guard:latest -f comps/guardrails/llm_guard_input_guardrail/impl/microservice/Dockerfile .
```

#### 2.2. Run the Docker container, for example:
```sh
docker run --e BAN_SUBSTRINGS_EMABLED="true" -p 8050:8050 opea/in-guard:latest
```

### 3. Verify the LLM Guard Input Guardrail Microservice

#### 3.1. Chaeck Status
```bash
curl http://localhost:8050/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### 3.2. Scanning using previously enabled scanners (for example via environmental variables) or while no scanner enabled

#### Example input
```bash
curl http://localhost:8050/v1/llmguardinput \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'
```

#### Example output (when no scanners enabled or scanner did not catch any problem)
```bash
{
    "id":"dded42f32bd9dddcb43bc0884d437faa",
    "model":null,"query":"What is Deep Learning?",
    "max_new_tokens":17,"top_k":10,"top_p":0.95,
    "typical_p":0.95,"temperature":0.01,
    "repetition_penalty":1.03,
    "streaming":false,
    "input_guardrail_params":null,
    "output_guardrail_params":null
}
```

### 3.3. Changing scanners configuration via requests

#### Example input
```bash
curl http://localhost:8050/v1/llmguardinput \
  -X POST \
  -d '{"query":"What are virus and backdoor?", 
        "max_new_tokens":17,
        "top_k":10,"top_p":0.95,
        "typical_p":0.95,
        "temperature":0.01,
        "repetition_penalty":1.03,
        "streaming":false,
        "input_guardrail_params":
            {"ban_substrings":
                {"enabled":true,
                "substrings":["backdoor","malware","virus"],
                "match_type":null,
                "case_sensitive":false,
                "redact":null,
                "contains_all":null}
            }
        }' \
  -H 'Content-Type: application/json'
```

#### Example output (when scanner blocked the prompt)
```bash
{
    "detail":"Prompt What are virus and backdoor? is not valid, scores: {'BanSubstrings': 1.0}"
}
```

A full set of possible configurations can be found in the file [object_document_mapper.py](src/comps/system_fingerprint/utils/object_document_mapper.py).

## Additional Information
### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the LLM Guard Input Guardrail Microservice.
- `utils/`: This directory contains scripts that are used by the LLM Guard Input Guardrail Microservice.

The tree view of the main directories and files:

```bash
├── README.md
├── impl
│   └── microservice
│       ├── .env
│       ├── Dockerfile
│       └── requirements.txt
├── opea_llm_guard_input_guardrail_microservice.py
└── utils
    ├── llm_guard_input_guardrail.py
    └── llm_guard_input_scanners.py
