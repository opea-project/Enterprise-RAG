# LLM Guard Output Guardrail Microservice
This microservice implements [LLM Guard](https://llm-guard.com/) (version: 0.3.14) Output Scanners as part of the pipeline. The goal is to enable Secure AI and privacy-related capabilities for Enterprise RAG. Output scanners scan LLM response and inform the user whether they are valid. LLM Guard OUtput Guardrail Microservice enables all scanners provided by LLM Guard:
 - [BanCode](https://llm-guard.com/output_scanners/ban_code/)
 - [BanCompetitors](https://llm-guard.com/output_scanners/ban_competitors/)
 - [BanSubstrings](https://llm-guard.com/output_scanners/ban_substrings/)
 - [BanTopics](https://llm-guard.com/output_scanners/ban_topics/)
 - [Bias](https://llm-guard.com/output_scanners/bias/)
 - [Code](https://llm-guard.com/output_scanners/code/)
 - [Deanonymize](https://llm-guard.com/output_scanners/deanonymize/)
 - [JSON](https://llm-guard.com/output_scanners/json/)
 - [Language](https://llm-guard.com/output_scanners/language/)
 - [LanguageSame](https://llm-guard.com/output_scanners/language_same/)
 - [MaliciousURLs](https://llm-guard.com/output_scanners/malicious_urls/)
 - [NoRefusal](https://llm-guard.com/output_scanners/no_refusal/)
 - [NoRefusalLight](https://llm-guard.com/output_scanners/no_refusal_light/)
 - [ReadingTime](https://llm-guard.com/output_scanners/reading_time/)
 - [FactualConsistency](https://llm-guard.com/output_scanners/factual_consistency/)
 - [Gibberish](https://llm-guard.com/output_scanners/gibberish/)
 - [Regex](https://llm-guard.com/output_scanners/regex/)
 - [Relevance](https://llm-guard.com/output_scanners/relevance/)
 - [Sensitive](https://llm-guard.com/output_scanners/sensitive/)
 - [Sentiment](https://llm-guard.com/output_scanners/sentiment/)
 - [Toxicity](https://llm-guard.com/output_scanners/toxicity/)
 - [URLReachability](https://llm-guard.com/output_scanners/url_reachability/)

A detailed description of each scanner is available on [LLM Guard](https://llm-guard.com/).

## Configuration Options
The scanners can be configured in two places: via UI and via environmental variables. There are five scanners enabled in UI. All scanners can be configured via environmental variables for the microservice.

### Configuration via UI
Scanners currently configurable from UI, from Admin Panel:
 - [BanCompetitors](https://llm-guard.com/output_scanners/ban_competitors/)
 - [BanSubstrings](https://llm-guard.com/output_scanners/ban_substrings/)
 - [Bias](https://llm-guard.com/output_scanners/bias/)
 - [Relevance](https://llm-guard.com/output_scanners/relevance/)

 Important: when LLM Guard Output Guardrail is enabled in Enterprise pipeline, LLM streaming option is not available, since LLM Guard Output Guardrail becomes reponsible for streaming. LLM Guard Output Guardrail waits for whole reponse from LLM to scan it.

### Configuration via environmental variables
The LLM Guard Output Guardrail Microservice configuration is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifying this dotenv file or exporting environmental variables as parameters to the container/pod. Each scanner can be configured in the .env file. Enabled scanners are executed sequentially. The environmental variables that are required for default run of particular scanner have values provided in .env file. Without providing them scanner will not work. The variables that do not have any values are optional, and without providing any values default values will be passed to scanner constructor.

### BanCode scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCode scanner](https://llm-guard.com/output_scanners/ban_code/)
| Environment Variable       | Description                                                | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_CODE_ENABLED`         | Enables BanCode scanner.                                   | bool   | "false"               | Required            |
| `BAN_CODE_USE_ONNX`        | Enables usage of ONNX optimized model for BanCode scanner. | bool   | "true"                | Required            |
| `BAN_CODE_MODEL`           | Model to be used for BanCode scanner.                      | string | "MODEL_SM"            | Optional            |
| `BAN_CODE_THRESHOLD`       | Threshold for BanCode scanner.                             | float  | 0.97                  | Optional            |

### BanCompetitors scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanCompetitors scanner](https://llm-guard.com/output_scanners/ban_competitors/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_COMPETITORS_ENABLED`  | Enables BanCompetitors scanner.                                               | bool   | "false"               | Required            |
| `BAN_COMPETITORS_USE_ONNX` | Enables usage of ONNX optimized model for BanCompetitors scanner.             | bool   | "true"                | Required            |
| `BAN_COMPETITORS_COMPETITORS` | List of competitors to be banned.                                          | string | "Competitor1,Competitor2,Competitor3" | Required |
| `BAN_COMPETITORS_THRESHOLD`| Threshold for BanCompetitors scanner.                                         | float  | 0.5                   | Optional            |
| `BAN_COMPETITORS_REDACT`   | Enables redaction of banned competitors.                                      | bool   | "true"                | Optional            |
| `BAN_COMPETITORS_MODEL`    | Model to be used for BanCompetitors scanner.                                  | string | "MODEL_V1"            | Optional            |

### BanSubstrings scanner
Detailed description of the scanner can be found in [LLM Guard documentation for BanSubstrings scanner](https://llm-guard.com/output_scanners/ban_substrings/)

| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_SUBSTRINGS_ENABLED`   | Enables BanSubstrings scanner.                                                | bool   | "false"               | Required            |
| `BAN_SUBSTRINGS_SUBSTRINGS`| List of substrings to be banned.                                              | string | "backdoor,malware,virus"| Required            |
| `BAN_SUBSTRINGS_MATCH_TYPE`| Match type for substrings.                                                    | string | "str"                 | Optional            |
| `BAN_SUBSTRINGS_CASE_SENSITIVE` | Enables case sensitivity for detecting substrings.                       | bool   | "false"               | Optional            |
| `BAN_SUBSTRINGS_REDACT`    | Enables redaction of banned substrings.                                       | bool   | "false"               | Optional            |
| `BAN_SUBSTRINGS_CONTAINS_ALL` | Requires all substrings to be present.                                     | bool   | "false"               | Optional            |

### BanTopics scanner

Detailed description of the scanner can be found in [LLM Guard documentation for BanTopics scanner](https://llm-guard.com/output_scanners/ban_topics/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `BAN_TOPICS_ENABLED`       | Enables BanTopics scanner.                                   | bool   | "false"               | Required            |
| `BAN_TOPICS_USE_ONNX`      | Enables usage of ONNX optimized model for BanTopics scanner. | bool   | "true"                | Required            |
| `BAN_TOPICS_TOPICS`        | List of topics to be banned.                                 | string | "violence,attack,war" | Required            |
| `BAN_TOPICS_THRESHOLD`     | Threshold for BanTopics scanner.                             | float  | 0.5                   | Optional            |
| `BAN_TOPICS_MODEL`         | Model to be used for BanTopics scanner.                      | string | "MODEL_V1"            | Optional            |

### Bias scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Bias scanner](https://llm-guard.com/output_scanners/bias/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `BIAS_ENABLED`             | Enables Bias scanner.                                                         | bool   | "false"               | Required            |
| `BIAS_USE_ONNX`            | Enables usage of ONNX optimized model for Bias scanner.                       | bool   | "true"                | Required            |
| `BIAS_MODEL`               | Model to be used for Bias scanner.                                            | string | "DEFAULT_MODEL"       | Optional            |
| `BIAS_THRESHOLD`           | Threshold for Bias scanner.                                                   | float  | 0.5                   | Optional            |
| `BIAS_MATCH_TYPE`          | Match type for Bias scanner.                                                  | string | "full"                | Optional            |

### Code scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Code scanner](https://llm-guard.com/output_scanners/code/)
| Environment Variable       | Description                                                 | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------|--------|-----------------------|---------------------|
| `CODE_ENABLED`             | Enables Code scanner.                                       | bool   | "false"               | Required            |
| `CODE_USE_ONNX`            | Enables usage of ONNX optimized model for Code scanner.     | bool   | "true"                | Required            |
| `CODE_LANGUAGES`           | List of programming languages to be detected.               | string | "Java,Python"         | Required            |
| `CODE_MODEL`               | Model to be used for Code scanner.                          | string | "DEFAULT_MODEL"       | Optional            |
| `CODE_IS_BLOCKED`          | Enables blocking of detected code.                          | bool   | "false"               | Optional            |
| `CODE_THRESHOLD`           | Threshold for Code scanner.                                 | float  | 0.5                   | Optional            |

### Deanonymize scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Deanonymize scanner](https://llm-guard.com/output_scanners/deanonymize/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `DEANONYMIZE_ENABLED`      | Enables Deanonymize scanner.                                                  | bool   | "false"               | Required            |
| `DEANONYMIZE_MATCHING_STRATEGY` | Matching strategy for Deanonymize scanner.                               | string | "exact"               | Optional            |

### JSON scanner

Detailed description of the scanner can be found in [LLM Guard documentation for JSON scanner](https://llm-guard.com/output_scanners/json/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `JSON_SCANNER_ENABLED`     | Enables JSON scanner.                                                         | bool   | "false"               | Required            |
| `JSON_SCANNER_REQUIRED_ELEMENTS` | The minimum number of JSON elements.                                    | int    | 0                     | Optional            |
| `JSON_SCANNER_REPAIR`      | Enables repair of JSON.                                                       | bool   | "false"               | Optional            |

### Language scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Language scanner](https://llm-guard.com/output_scanners/language/)
| Environment Variable                | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `LANGUAGE_ENABLED`                  | Enables Language scanner.                                    | bool   | "false"               | Required            |
| `LANGUAGE_USE_ONNX`                 | Enables usage of ONNX optimized model for Language scanner.  | bool   | "true"                | Required            |
| `LANGUAGE_VALID_LANGUAGES`          | List of supported languages for the Language scanner.        | string | "en,es"               | required            |
| `LANGUAGE_MODEL`                    | Model to be used for Language scanner.                       | string | "DEFAULT_MODEL"       | Optional            |
| `LANGUAGE_THRESHOLD`                | Threshold for Language scanner.                              | float  | 0.6                   | Optional            |
| `LANGUAGE_MATCH_TYPE`               | Match type for language detection (e.g., full, partial).     | string | "full"                | Optional            |

### LanguageSame scanner

Detailed description of the scanner can be found in [LLM Guard documentation for LanguageSame scanner](https://llm-guard.com/output_scanners/language_same/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|--------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `LANGUAGE_SAME_ENABLED`    | Enables LanguageSame scanner.                                                 | bool   | "false"               | Required            |
| `LANGUAGE_SAME_USE_ONNX`   | Enables usage of ONNX optimized model for LanguageSame scanner.               | bool   | "true"                | Required            |
| `LANGUAGE_SAME_MODEL`      | Model to be used for LanguageSame scanner.                                    | string | "DEFAULT_MODEL"       | Optional            |
| `LANGUAGE_SAME_THRESHOLD`  | Threshold for LanguageSame scanner.                                           | float  | 0.1                   | Optional            |

### MaliciousURLs scanner

Detailed description of the scanner can be found in [LLM Guard documentation for MaliciousURLs scanner](https://llm-guard.com/output_scanners/malicious_urls/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|--------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `MALICIOUS_URLS_ENABLED`   | Enables MaliciousURLs scanner.                                                | bool   | "false"               | Required            |
| `MALICIOUS_URLS_USE_ONNX`  | Enables usage of ONNX optimized model for MaliciousURLs scanner. Default: "true".| bool   | "true"                | Required            |
| `MALICIOUS_URLS_MODEL`     | Model to be used for MaliciousURLs scanner. Default: "DEFAULT_MODEL".         | string | "DEFAULT_MODEL"       | Optional            |
| `MALICIOUS_THRESHOLD`      | Threshold for MaliciousURLs scanner.                                          | float  | 0.5                   | Optional            |

### NoRefusal scanner

Detailed description of the scanner can be found in [LLM Guard documentation for NoRefusal scanner](https://llm-guard.com/output_scanners/no_refusal/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|--------------------------- |--------------------------------------------------------------|--------|-----------------------|---------------------|
| `NO_REFUSAL_ENABLED`       | Enables NoRefusal scanner.                                   | bool   | "false"               | Required            |
| `NO_REFUSAL_USE_ONNX`      | Enables usage of ONNX optimized model for NoRefusal scanner. | bool   | "true"                | Required            |
| `NO_REFUSAL_MODEL`         | Model to be used for NoRefusal scanner.                      | string | "DEFAULT_MODEL"       | Optional            |
| `NO_REFUSAL_THRESHOLD`     | Threshold for NoRefusal scanner.                             | float  | 0.75                  | Optional            |
| `NO_REFUSAL_MATCH_TYPE`    | Match type for NoRefusal scanner.                            | string | "full"                | Optional            |

### NoRefusalLight scanner

| Environment Variable            | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `NO_REFUSAL_LIGHT_ENABLED`      | Enables NoRefusalLight scanner.                                               | bool   | "false"               | Required            |
| `NO_REFUSAL_LIGHT_SUBSTRINGS`   | List of substrings to be banned.                                              | string | [LLMGuard documentation](https://github.com/protectai/llm-guard/blob/main/llm_guard/output_scanners/no_refusal.py#L120)              | Optional            |
| `NO_REFUSAL_LIGHT_MATCH_TYPE`   | Match type for substrings.                                                    | string | "str"                 | Optional            |
| `NO_REFUSAL_LIGHT_CASE_SENSITIVE` | Enables case sensitivity for substrings.                                    | bool   | "false"               | Optional            |
| `NO_REFUSAL_LIGHT_REACT`        | Enables redaction of banned substrings.                                       | bool   | "false"               | Optional            |
| `NO_REFUSAL_LIGHT_CONTAINS_ALL` | Requires all substrings to be present.                                        | bool   | "false"               | Optional            |


### ReadingTime scanner

Detailed description of the scanner can be found in [LLM Guard documentation for ReadingTime scanner](https://llm-guard.com/output_scanners/reading_time/)
| Environment Variable       | Description                                               | Type   | Default in LLM Guard  | Required / Optional |
|--------------------------- |-----------------------------------------------------------|--------|-----------------------|---------------------|
| `READING_TIME_ENABLED`     | Enables ReadingTime scanner.                              | bool   | "false"               | Required            |
| `READING_TIME_MAX_TIME`    | Maximum reading time allowed.                             | float  | no value              | Required            |
| `READING_TIME_TRUNCATE`    | Enables truncation if reading time exceeds the limit.     | bool   | "false"               | Optional            |

### FactualConsistency scanner

Detailed description of the scanner can be found in [LLM Guard documentation for FactualConsistency scanner](https://llm-guard.com/output_scanners/factual_consistency/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard   | Required / Optional |
|--------------------------- |-------------------------------------------------------------------------------|--------|------------------------|---------------------|
| `FACTUAL_CONSISTENCY_ENABLED` | Enables FactualConsistency scanner.                                        | bool   | "false"                | Required            |
| `FACTUAL_CONSISTENCY_USE_ONNX` | Enables usage of ONNX optimized model for FactualConsistency scanner.     | bool   | "true"                 | Required            |
| `FACTUAL_CONSISTENCY_MODEL` | Model to be used for FactualConsistency scanner.                             | string | "MODEL_DEBERTA_BASE_V2"| Optional            |
| `FACTUAL_CONSISTENCY_MINIMUM_SCORE` | Minimum score for FactualConsistency scanner.                        | float  | 0.75                   | Optional            |

### Gibberish scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Gibberish scanner](https://llm-guard.com/output_scanners/gibberish/)
| Environment Variable       | Description                                                  | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|--------------------------------------------------------------|--------|-----------------------|---------------------|
| `GIBBERISH_ENABLED`        | Enables Gibberish scanner.                                   | bool   | "false"               | Required            |
| `GIBBERISH_USE_ONNX`       | Enables usage of ONNX optimized model for Gibberish scanner. | bool   | "true"                | Required            |
| `GIBBERISH_MODEL`          | Model to be used for Gibberish scanner.                      | string | "DEFAULT_MODEL"       | Optional            |
| `GIBBERISH_THRESHOLD`      | Threshold for Gibberish scanner.                             | float  | 0.5                   | Optional            |
| `GIBBERISH_MATCH_TYPE`     | Whether to match the full text or individual sentences.      | string | "full"                | Optional            |

### Regex scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Regex scanner](https://llm-guard.com/output_scanners/regex/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `REGEX_ENABLED`            | Enables Regex scanner.                                                        | bool   | "false"               | Required            |
| `REGEX_PATTERNS`           | List of regex patterns to be used.                                            | string | "Bearer [A-Za-z0-9-._~+/]+"| Required            |
| `REGEX_IS_BLOCKED`         | Enables blocking of matched patterns.                                         | bool   | "true"               | Optional            |
| `REGEX_MATCH_TYPE`         | Match type for regex patterns (e.g., full, partial).                          | string | "SEARCH"              | Optional            |
| `REGEX_REDACT`             | Enables redaction of output.                                                  | bool   | "false"               | Optional            |

### Relevance scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Relevance scanner](https://llm-guard.com/output_scanners/relevance/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|--------------------------- |-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `RELEVANCE_ENABLED`        | Enables Relevance scanner.                                                    | bool   | "false"               | Required            |
| `RELEVANCE_USE_ONNX`       | Enables usage of ONNX optimized model for Relevance scanner.                  | bool   | "true"                | Required            |
| `RELEVANCE_MODEL`          | Model to be used for Relevance scanner.                                       | string | "MODEL_EN_BGE_BAS"    | Optional            |
| `RELEVANCE_THRESHOLD`      | Threshold for Relevance scanner.                                              | float  | 0.5                   | Optional            |

### Sensitive scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Sensitive scanner](https://llm-guard.com/output_scanners/sensitive/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SENSITIVE_ENABLED`        | Enables Sensitive scanner.                                                    | bool   | "false"               | Required            |
| `SENSITIVE_USE_ONNX`       | Enables usage of ONNX optimized model for Sensitive scanner.                  | bool   | "true"                | Required            |
| `SENSITIVE_ENTITY_TYPES`   | List of entity types to be recognized.                                        | string | no value              | Optional            |
| `SENSITIVE_REGEX_PATTERNS` | List of regex patterns to be used.                                            | string |  [LLMGuard documentation](https://github.com/protectai/llm-guard/blob/main/llm_guard/output_scanners/sensitive.py#L40)                            | Optional            |
| `SENSITIVE_REDACT`         | Enables redaction of sensitive information.                                   | bool   | "false"               | Optional            |
| `SENSITIVE_RECOGNIZER_CONF`| Configuration for custom recognizers.                                         | string | [LLMGuard documentation](https://github.com/protectai/llm-guard/blob/main/llm_guard/output_scanners/sensitive.py#L42)              | Optional            |
| `SENSITIVE_THRESHOLD`      | Threshold for Sensitive scanner.                                              | float  | 0.5                   | Optional            |

### Sentiment scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Sentiment scanner](https://llm-guard.com/output_scanners/sentiment/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `SENTIMENT_ENABLED`        | Enables Sentiment scanner.                                                    | bool   | "false"               | Required            |
| `SENTIMENT_THRESHOLD`      | Threshold for Sentiment scanner.                                              | float  | -0.1                  | Optional            |
| `SENTIMENT_LEXICON`        | Lexicon to be used for sentiment analysis.                                    | string | "vader_lexicon"       | Optional            |

### Toxicity scanner

Detailed description of the scanner can be found in [LLM Guard documentation for Toxicity scanner](https://llm-guard.com/output_scanners/toxicity/)
| Environment Variable       | Description                                                                   | Type   | Default in LLM Guard  | Required / Optional |
|----------------------------|-------------------------------------------------------------------------------|--------|-----------------------|---------------------|
| `TOXICITY_ENABLED`         | Enables Toxicity scanner.                                                     | bool   | "false"               | Required            |
| `TOXICITY_USE_ONNX`        | Enables usage of ONNX optimized model for Toxicity scanner.                   | bool   | "true"                | Required            |
| `TOXICITY_MODEL`           | Model to be used for Toxicity scanner.                                        | string | "DEFAULT_MODEL"       | Optional            |
| `TOXICITY_THRESHOLD`       | Threshold for Toxicity scanner.                                               | float  | 0.5                   | Optional            |
| `TOXICITY_MATCH_TYPE`      | Match type for toxicity detection.                                            | string | "full"                | Optional            |

### URLReachability scanner

Detailed description of the scanner can be found in [LLM Guard documentation for URLReachability scanner](https://llm-guard.com/output_scanners/url_reachability/)
| Environment Variable                      | Description                                        | Type   | Default in LLM Guard  | Required / Optional |
|-------------------------------------------|----------------------------------------------------|--------|-----------------------|---------------------|
| `URL_REACHABILITY_ENABLED`                | Enables URLReachability scanner.                   | bool   | "false"               | Required            |
| `URL_REACHABILITY_SUCCESS_STATUS_CODES`   | List of HTTP status codes considered as successful.| string | no value              | Optional            |
| `URL_REACHABILITY_TIMEOUT`                | Timeout for URL reachability check in seconds.     | int    | 5                     | Optional            |

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

```bash
pip install -r impl/microservice/requirements.txt
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
    docker run --e BAN_SUBSTRINGS_EMABLED="true" -p 8060:8060 opea/out-guard:latest
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
```bash
{
    "detail":"Prompt What are virus and backdoor? is not valid, scores: {'BanSubstrings': 1.0}"
}
```

## Additional Information

### Project Structure

The project is organized into several directories:

- `impl/`: This directory contains configuration files for the LLM Guard Output Guardrail Microservice.
- `utils/`: This directory contains scripts that are used by the LLM Guard Output Guardrail Microservice.

The tree view of the main directories and files:

```bash
├── README.md
├── impl
│   └── microservice
│       ├── .env
│       ├── Dockerfile
│       └── requirements.txt
├── opea_llm_guard_output_guardrail_microservice.py
└── utils
    ├── llm_guard_output_guardrail.py
    └── llm_guard_output_scanners.py
