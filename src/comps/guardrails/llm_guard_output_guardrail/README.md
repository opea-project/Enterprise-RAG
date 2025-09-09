# LLM Guard Output Guardrail Microservice
This microservice implements [LLM Guard](https://protectai.github.io/llm-guard/) (version: 0.3.16) Output Scanners as part of the pipeline. The goal is to enable Secure AI and privacy-related capabilities for Enterprise RAG. Output scanners scan LLM response and inform the user whether they are valid. LLM Guard OUtput Guardrail Microservice enables all scanners provided by LLM Guard:
 - [BanSubstrings](#bansubstrings-scanner)
 - [BanTopics](#bantopics-scanner)
 - [Bias](#bias-scanner)
 - [Code](#code-scanner)
 - [Deanonymize](#deanonymize-scanner)
 - [JSON](#json-scanner)
 - [MaliciousURLs](#maliciousurls-scanner)
 - [NoRefusal](#norefusal-scanner)
 - [NoRefusalLight](#norefusallight-scanner)
 - [ReadingTime](#readingtime-scanner)
 - [FactualConsistency](#factualconsistency-scanner)
 - [Regex](#regex-scanner)
 - [Relevance](#relevance-scanner)
 - [Sensitive](#sensitive-scanner)
 - [Sentiment](#sentiment-scanner)
 - [Toxicity](#toxicity-scanner)
 - [URLReachability](#urlreachability-scanner)

A detailed description of each scanner is available on [LLM Guard](https://protectai.github.io/llm-guard/).

## Configuration Options
The scanners can be configured in two places: via UI and via environmental variables. There are seven scanners enabled in UI. All scanners can be configured via environmental variables for the microservice.

### Configuration via UI

> [!Warning]
> Output guardrail is not enabled in default Chatqna's pipeline. To run a pipeline with output guardrails, check out custom pipelines in [deployment/pipelines/chatqa/examples](../../../../deployment/pipelines/chatqa/examples).

Scanners currently configurable from UI, from Admin Panel:
 - [BanSubstrings](#bansubstrings-scanner) - fully configurable
 - [Code](#code-scanner) - partially configurable
 - [Bias](#bias-scanner) - partially configurable
 - [Relevance](#relevance-scanner) - partially configurable
 - [MaliciousURLs](#maliciousurls-scanner) - partially configurable

### Configuration via environmental variables
The LLM Guard Output Guardrail Microservice configuration is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or exporting environmental variables as parameters to the container/pod. Each scanner can be configured in the .env file. Enabled scanners are executed sequentially. The environmental variables that are required for default run of particular scanner have values provided in .env file. Without providing them scanner will not work. The variables that do not have any values are optional, and without providing any values default values will be passed to scanner constructor.

### BanSubstrings scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanSubstrings scanner](https://protectai.github.io/llm-guard/output_scanners/ban_substrings/)

| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `BAN_SUBSTRINGS_ENABLED`   | Enables BanSubstrings scanner.                                                | bool   | false               | Required            | Yes |
| `BAN_SUBSTRINGS_SUBSTRINGS`| List of substrings to be banned.                                              | string(list can be also in one string with elements separated with commas)/List[string] | "backdoor,malware,virus"| Required            | Yes |
| `BAN_SUBSTRINGS_MATCH_TYPE`| Match type for substrings.                                                    | string | "str"                 | Optional            | Yes |
| `BAN_SUBSTRINGS_CASE_SENSITIVE` | Enables case sensitivity for detecting substrings.                       | bool   | false               | Optional            | Yes |
| `BAN_SUBSTRINGS_REDACT`    | Enables redaction of banned substrings.                                       | bool   | false               | Optional            | Yes |
| `BAN_SUBSTRINGS_CONTAINS_ALL` | Requires all substrings to be present.                                     | bool   | false               | Optional            | Yes |

### BanTopics scanner

Detailed description of the scanner can be found in [LLM Guard documentation for BanTopics scanner](https://protectai.github.io/llm-guard/output_scanners/ban_topics/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `BAN_TOPICS_ENABLED`       | Enables BanTopics scanner.                                   | bool   | false               | Required            | No |
| `BAN_TOPICS_USE_ONNX`      | Enables usage of ONNX optimized model for BanTopics scanner. | bool   | false                | Required            | No |
| `BAN_TOPICS_TOPICS`        | List of topics to be banned.                                 | string(list can be also in one string with elements separated with commas)/List[string] | "violence,attack,war" | Required            | No |
| `BAN_TOPICS_THRESHOLD`     | Threshold for BanTopics scanner.                             | float  | 0.6                   | Optional            | No |
| `BAN_TOPICS_MODEL`         | Model to be used for BanTopics scanner.                      | string | none            | Optional            | No |

### Bias scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Bias scanner](https://protectai.github.io/llm-guard/output_scanners/bias/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `BIAS_ENABLED`             | Enables Bias scanner.                                                         | bool   | false               | Required            | Yes |
| `BIAS_USE_ONNX`            | Enables usage of ONNX optimized model for Bias scanner.                       | bool   | false                | Required            | No |
| `BIAS_MODEL`               | Model to be used for Bias scanner.                                            | string | none       | Optional            | No |
| `BIAS_THRESHOLD`           | Threshold for Bias scanner.                                                   | float  | none                   | Optional            | Yes |
| `BIAS_MATCH_TYPE`          | Match type for Bias scanner.                                                  | string | none                | Optional            | Yes |

### Code scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Code scanner](https://protectai.github.io/llm-guard/output_scanners/code/)
| Environment Variable       | Description                                                 | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `CODE_ENABLED`             | Enables Code scanner.                                       | bool   | false               | Required            | Yes |
| `CODE_USE_ONNX`            | Enables usage of ONNX optimized model for Code scanner.     | bool   | false                | Required            | No |
| `CODE_LANGUAGES`           | List of programming languages to be detected.               | string(list can be also in one string with elements separated with commas)/List[string] | "Java,Python"         | Required            | Yes |
| `CODE_MODEL`               | Model to be used for Code scanner.                          | string | none       | Optional            | No |
| `CODE_IS_BLOCKED`          | Enables blocking of detected code.                          | bool   | false               | Optional            | No |
| `CODE_THRESHOLD`           | Threshold for Code scanner.                                 | float  | 0.5                   | Optional            | Yes |

### Deanonymize scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Deanonymize scanner](https://protectai.github.io/llm-guard/output_scanners/deanonymize/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `DEANONYMIZE_ENABLED`      | Enables Deanonymize scanner.                                                  | bool   | false               | Required            | No |
| `DEANONYMIZE_MATCHING_STRATEGY` | Matching strategy for Deanonymize scanner.                               | string | none               | Optional            | No |

### JSON scanner

Detailed description of the scanner can be found in [LLM Guard documentation for JSON scanner](https://protectai.github.io/llm-guard/output_scanners/json/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `JSON_SCANNER_ENABLED`     | Enables JSON scanner.                                                         | bool   | false               | Required            | No |
| `JSON_SCANNER_REQUIRED_ELEMENTS` | The minimum number of JSON elements.                                    | int    | none                     | Optional            | No |
| `JSON_SCANNER_REPAIR`      | Enables repair of JSON.                                                       | bool   | false               | Optional            | No |

### MaliciousURLs scanner

Detailed description of the scanner can be found in [LLM Guard documentation for MaliciousURLs scanner](https://protectai.github.io/llm-guard/output_scanners/malicious_urls/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|--------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `MALICIOUS_URLS_ENABLED`   | Enables MaliciousURLs scanner.                                                | bool   | false               | Required            | Yes |
| `MALICIOUS_URLS_USE_ONNX`  | Enables usage of ONNX optimized model for MaliciousURLs scanner. Default: false.| bool   | false                | Required            | No |
| `MALICIOUS_URLS_MODEL`     | Model to be used for MaliciousURLs scanner. Default: "DEFAULT_MODEL".         | string | none       | Optional            | No |
| `MALICIOUS_THRESHOLD`      | Threshold for MaliciousURLs scanner.                                          | float  | none                   | Optional            | Yes |

### NoRefusal scanner

Detailed description of the scanner can be found in [LLM Guard documentation for NoRefusal scanner](https://protectai.github.io/llm-guard/output_scanners/no_refusal/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|--------------------------- |--------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `NO_REFUSAL_ENABLED`       | Enables NoRefusal scanner.                                   | bool   | false               | Required            | No |
| `NO_REFUSAL_USE_ONNX`      | Enables usage of ONNX optimized model for NoRefusal scanner. | bool   | false                | Required            | No |
| `NO_REFUSAL_MODEL`         | Model to be used for NoRefusal scanner.                      | string | none       | Optional            | No |
| `NO_REFUSAL_THRESHOLD`     | Threshold for NoRefusal scanner.                             | float  | none                  | Optional            | No |
| `NO_REFUSAL_MATCH_TYPE`    | Match type for NoRefusal scanner.                            | string | none                | Optional            | No |

### NoRefusalLight scanner

| Environment Variable            | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|-------------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `NO_REFUSAL_LIGHT_ENABLED`      | Enables NoRefusalLight scanner.                                               | bool   | false               | Required            | No |

### ReadingTime scanner

Detailed description of the scanner can be found in [LLM Guard documentation for ReadingTime scanner](https://protectai.github.io/llm-guard/output_scanners/reading_time/)
| Environment Variable       | Description                                               | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|--------------------------- |-----------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `READING_TIME_ENABLED`     | Enables ReadingTime scanner.                              | bool   | false               | Required            | No |
| `READING_TIME_MAX_TIME`    | Maximum reading time allowed.                             | float  | 0.5              | Required            | No |
| `READING_TIME_TRUNCATE`    | Enables truncation if reading time exceeds the limit.     | bool   | false               | Optional            | No |

### FactualConsistency scanner

Detailed description of the scanner can be found in [LLM Guard documentation for FactualConsistency scanner](https://protectai.github.io/llm-guard/output_scanners/factual_consistency/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard   | Required / Optional | Available in Chatqna's UI |
|--------------------------- |-------------------------------------------------------------------------------|--------|------------------------|---------------------|---------------------|
| `FACTUAL_CONSISTENCY_ENABLED` | Enables FactualConsistency scanner.                                        | bool   | false                | Required            | No |
| `FACTUAL_CONSISTENCY_USE_ONNX` | Enables usage of ONNX optimized model for FactualConsistency scanner.     | bool   | false                 | Required            | No |
| `FACTUAL_CONSISTENCY_MODEL` | Model to be used for FactualConsistency scanner.                             | string | none | Optional            | No |
| `FACTUAL_CONSISTENCY_MINIMUM_SCORE` | Minimum score for FactualConsistency scanner.                        | float  | none                   | Optional            | No |

### Regex scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Regex scanner](https://protectai.github.io/llm-guard/output_scanners/regex/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `REGEX_ENABLED`            | Enables Regex scanner.                                                        | bool   | false               | Required            | No |
| `REGEX_PATTERNS`           | List of regex patterns to be used.                                            | string | "Bearer [A-Za-z0-9-._~+/]+"| Required            | No |
| `REGEX_IS_BLOCKED`         | Enables blocking of matched patterns.                                         | bool   | false               | Optional            | No |
| `REGEX_MATCH_TYPE`         | Match type for regex patterns (e.g., full, partial).                          | string | "all"              | Optional            | No |
| `REGEX_REDACT`             | Enables redaction of output.                                                  | bool   | false               | Optional            | No |

### Relevance scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Relevance scanner](https://protectai.github.io/llm-guard/output_scanners/relevance/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|--------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `RELEVANCE_ENABLED`        | Enables Relevance scanner.                                                    | bool   | false               | Required            | Yes |
| `RELEVANCE_USE_ONNX`       | Enables usage of ONNX optimized model for Relevance scanner.                  | bool   | false                | Required            | No |
| `RELEVANCE_MODEL`          | Model to be used for Relevance scanner.                                       | string | none    | Optional            | No |
| `RELEVANCE_THRESHOLD`      | Threshold for Relevance scanner.                                              | float  | none                   | Optional            | Yes |

### Sensitive scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Sensitive scanner](https://protectai.github.io/llm-guard/output_scanners/sensitive/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `SENSITIVE_ENABLED`        | Enables Sensitive scanner.                                                    | bool   | false               | Required            | No |
| `SENSITIVE_USE_ONNX`       | Enables usage of ONNX optimized model for Sensitive scanner.                  | bool   | false                | Required            | No |
| `SENSITIVE_ENTITY_TYPES`   | List of entity types to be recognized.                                        | string(list can be also in one string with elements separated with commas)/List[string] | none              | Optional            | No |
| `SENSITIVE_REGEX_PATTERNS` | List of regex patterns to be used.                                            | string(list can be also in one string with elements separated with commas)/List[string] |  [LLMGuard documentation](https://github.com/protectai/llm-guard/blob/main/llm_guard/output_scanners/sensitive.py#L40)                            | Optional            | No |
| `SENSITIVE_REDACT`         | Enables redaction of sensitive information.                                   | bool   | false               | Optional            | No |
| `SENSITIVE_RECOGNIZER_CONF`| Configuration for custom recognizers.                                         | string | [LLMGuard documentation](https://github.com/protectai/llm-guard/blob/main/llm_guard/output_scanners/sensitive.py#L42)              | Optional            |
| `SENSITIVE_THRESHOLD`      | Threshold for Sensitive scanner.                                              | float  | none                   | Optional            | No |

### Sentiment scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Sentiment scanner](https://protectai.github.io/llm-guard/output_scanners/sentiment/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `SENTIMENT_ENABLED`        | Enables Sentiment scanner.                                                    | bool   | false               | Required            | No |
| `SENTIMENT_THRESHOLD`      | Threshold for Sentiment scanner.                                              | float  | -0.3                  | Optional            | No |
| `SENTIMENT_LEXICON`        | Lexicon to be used for sentiment analysis.                                    | string | none       | Optional            | No |

### Toxicity scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Toxicity scanner](https://protectai.github.io/llm-guard/output_scanners/toxicity/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `TOXICITY_ENABLED`         | Enables Toxicity scanner.                                                     | bool   | false               | Required            | No |
| `TOXICITY_USE_ONNX`        | Enables usage of ONNX optimized model for Toxicity scanner.                   | bool   | false                | Required            | No |
| `TOXICITY_MODEL`           | Model to be used for Toxicity scanner.                                        | string | none       | Optional            | No |
| `TOXICITY_THRESHOLD`       | Threshold for Toxicity scanner.                                               | float  | 0.5                   | Optional            | No |
| `TOXICITY_MATCH_TYPE`      | Match type for toxicity detection.                                            | string | "full"                | Optional            | No |

### URLReachability scanner

Detailed description of the scanner can be found in [LLM Guard documentation for URLReachability scanner](https://protectai.github.io/llm-guard/output_scanners/url_reachability/)
| Environment Variable                      | Description                                        | Type   | Default in LLM Guard  | Required / Optional | Available in Chatqna's UI |
|-------------------------------------------|----------------------------------------------------|--------|-----------------------|---------------------|---------------------|
| `URL_REACHABILITY_ENABLED`                | Enables URLReachability scanner.                   | bool   | false               | Required            | No |
| `URL_REACHABILITY_SUCCESS_STATUS_CODES`   | List of HTTP status codes considered as successful.| string | none              | Optional            | No |
| `URL_REACHABILITY_TIMEOUT`                | Timeout for URL reachability check in seconds.     | int    | none                     | Optional            | No |

## Getting started

### Prerequisites

1. **Navigate to the microservice directory**:
    ```sh
    cd src/comps/guardrails/llm_guard_output_guardrail
    ```

2. **Set up the environment variables**:
    - Edit the `.env` file to configure the necessary environment variables for the scanners you want to enable.

### 🚀1. Start LLM Guard Output Guardrail Microservice with Python (Option 1)

To start the LLM Guard Output Guardrail microservice, you need to install python packages first.

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
python opea_llm_guard_output_guardrail_microservice.py
```

### 🚀2. Start LLM Guard Output Guardrail Microservice with Docker (Option 2)

#### 2.1.Build the Docker image:
```sh
cd ../../.. # src/ directory
docker build -t opea/out-guard:latest -f comps/guardrails/llm_guard_output_guardrail/impl/microservice/Dockerfile .
```

#### 2.2. Run the Docker container, for example:
```sh
docker run --rm -p 8060:8060 --name="llm-guard-output-microservice" opea/out-guard:latest
```

### 3. Verify the LLM Guard Input Guardrail Microservice

#### 3.2. Chaeck Status
```bash
curl http://localhost:8060/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

#### 3.2. Scanning using previously enabled scanners (for example via environmental variables) or while no scanner enabled

#### Example input
```bash
curl http://localhost:8060/v1/llmguardoutput \
  -X POST \
  -d '{"prompt":"What is Deep Learning?", "text": "Some random LLM response"}' \
  -H 'Content-Type: application/json'
```

#### Example output (when no scanners enabled or scanner did not catch any problem)
```bash
data: ' Some'
data: ' random'
data: ' LLM'
data: ' response'
data: '[DONE]'
```

If additional data is passed then it is appended at the end of the response in the following way:

```bash
data: ' Some'
data: ' random'
data: ' LLM'
data: ' response'
data: '[DONE]'
json: '{ "reranked_docs": [{ "url": "https://example.com", "citation_id": 1, "vector_distance": 0.23, "reranker_score": 0.83 }] }'
```

### 3.3. Changing scanners configuration via requests

#### Example input
```bash
curl http://localhost:8060/v1/llmguardoutput \
  -X POST \
  -d '{"prompt":"What is Deep Learning?",
        "text": "To create a virus and backdoor you need to...",
        "output_guardrail_params":
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

A full set of possible configurations can be found in the file [object_document_mapper.py](src/comps/system_fingerprint/utils/object_document_mapper.py).

#### Example output (when scanner blocked the prompt)
The output of an output guardrail microservice is a 466 error code JSON object that includes following message.

```bash
{
    {
        "detail":"I'm sorry, I cannot assist you with your prompt."
    }
}
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the LLM Guard Output Guardrail Microservice e.g. docker files.
- `utils/`: This directory contains scripts that are used by the LLM Guard Output Guardrail Microservice.
