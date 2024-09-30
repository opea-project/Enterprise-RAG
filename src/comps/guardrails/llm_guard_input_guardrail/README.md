# OPEA LLM Guard Input Guardrail Microservice
This microservice implements [LLM Guard](https://llm-guard.com/) Input Scanners as part OPEA pipeline. It enables all scanners provided by LLM Guard:
[Anonymize](https://llm-guard.com/input_scanners/anonymize/), [BanCode](https://llm-guard.com/input_scanners/ban_code/), [BanCompetitors](https://llm-guard.com/input_scanners/ban_competitors/), [BanSubstrings](https://llm-guard.com/input_scanners/ban_substrings/), [BanTopics](https://llm-guard.com/input_scanners/ban_topics/), [Code](https://llm-guard.com/input_scanners/code/), [Gibberish](https://llm-guard.com/input_scanners/gibberish/), [InvisibleText](https://llm-guard.com/input_scanners/invisible_text/), [Language](https://llm-guard.com/input_scanners/language/), [PromptInjection](https://llm-guard.com/input_scanners/prompt_injection/), [Regex](https://llm-guard.com/input_scanners/regex/), [Secrets](https://llm-guard.com/input_scanners/secrets/), [Sentiment](https://llm-guard.com/input_scanners/sentiment/), [TokenLimit](https://llm-guard.com/input_scanners/token_limit/), [Toxcity](https://llm-guard.com/input_scanners/toxicity/)
Detailed escription of each scanner is available on [LLM Guard](https://llm-guard.com/) website.

## Configuration Options
The configuration for the OPEA LLM Guard Input Guardrail Microservice is specified in the [impl/microservice/.env](impl/microservice/.env) file. You can adjust these settings by modifing this dotenv file or by exporting environment variables. Each scanner can be configured in .env file. Enabled scanners are executed sequentially.

| Environment Variable      | Description                                                                   |
|---------------------------|-------------------------------------------------------------------------------|
| `ANONYMIZE_ENABLED`       | Enables Anonymize scanner. Default: False.                                    |
| `ANONYMIZE_USE_ONNX`      | Enables usage of ONNX optimized model for Anonymize scanner. Default: True.   |
| `ANONYMIZE_HIDDEN_NAMES`  | List of names to be anonymized e.g. [REDACTED_CUSTOM_1]. Default: None.       |
| `ANONYMIZE_ALLOWED_NAMES` | List of names allowed in the text without anonymizing. Default:None.          |
| `ANONYMIZE_ENTITY_TYPES`  | TBD              |

# Getting started
TODO: to be added