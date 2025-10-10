# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pydantic import model_validator, PositiveInt, NonNegativeFloat
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from beanie import Document, PydanticObjectId


class AnonymizeModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    hidden_names: Optional[List[str]] = None
    allowed_names: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    preamble: Optional[str] = None
    regex_patterns: Optional[List[str]] = None
    use_faker: Optional[bool] = False
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None
    language: Optional[str] = None


class BanSubstringsModel(Document):
    enabled: bool = False
    substrings: List[str] = ["backdoor", "malware", "virus"]
    match_type: Optional[str] = "str"
    case_sensitive: bool = False
    redact: Optional[bool] = False
    contains_all: Optional[bool] = False


class BanTopicsModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    topics: List[str] = ["violence", "attack", "war"]
    threshold: Optional[float] = 0.6
    model: Optional[str] = None


class CodeModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    languages: List[str] = ["Java", "Python"]
    model: Optional[str] = None
    is_blocked: Optional[bool] = True
    threshold: Optional[float] = 0.5


class InvisibleText(Document):
    enabled: bool = False


class PromptInjectionModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = 0.92
    match_type: Optional[str] = "full"


class RegexModel(Document):
    enabled: bool = False
    patterns: List[str] = ["Bearer [A-Za-z0-9-._~+/]+"]
    is_blocked: Optional[bool] = True
    match_type: Optional[str] = "all"
    redact: Optional[bool] = False


class SecretsModel(Document):
    enabled: bool = False
    redact_mode: Optional[str] = "all"


class SentimentModel(Document):
    enabled: bool = False
    threshold: Optional[float] = -0.3
    lexicon: Optional[str] = None


class TokenLimitModel(Document):
    enabled: bool = False
    limit: Optional[int] = 4096
    encoding_name: Optional[str] = "cl100k_base"
    model_name: Optional[str] = None


class ToxicityModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = 0.5
    match_type: Optional[str] = "full"


class BiasModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class DeanonymizeModel(Document):
    enabled: bool = False
    matching_strategy: Optional[str] = None


class JSONModel(Document):
    enabled: bool = False
    required_elements: Optional[int] = None
    repair: Optional[bool] = False


class MaliciousURLsModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None


class NoRefusalModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class NoRefusalLightModel(Document):
    enabled: bool = False


class ReadingTimeModel(Document):
    enabled: bool = False
    max_time: float = 0.5
    truncate: Optional[bool] = False


class FactualConsistencyModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    minimum_score: Optional[float] = None


class RelevanceModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None


class SensitiveModel(Document):
    enabled: bool = False
    use_onnx: bool = False
    entity_types: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None
    redact: Optional[bool] = False
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None


class URLReachabilityModel(Document):
    enabled: bool = False
    success_status_codes: Optional[List[int]] = None
    timeout: Optional[int] = None


class LLMGuardInputGuardrailParams(Document):
    anonymize: AnonymizeModel = None
    ban_substrings: BanSubstringsModel = None
    ban_topics: BanTopicsModel = None
    code: CodeModel = None
    invisible_text: InvisibleText = None
    prompt_injection: PromptInjectionModel = None
    regex: RegexModel = None
    secrets: SecretsModel = None
    sentiment: SentimentModel = None
    token_limit: TokenLimitModel = None
    toxicity: ToxicityModel = None


class LLMGuardOutputGuardrailParams(Document):
    ban_substrings: BanSubstringsModel = None
    ban_topics: BanTopicsModel = None
    bias: BiasModel = None
    code: CodeModel = None
    deanonymize: DeanonymizeModel = None
    json_scanner: JSONModel = None
    malicious_urls: MaliciousURLsModel = None
    no_refusal: NoRefusalModel = None
    no_refusal_light: NoRefusalLightModel = None
    reading_time: ReadingTimeModel = None
    factual_consistency: FactualConsistencyModel = None
    regex: RegexModel = None
    relevance: RelevanceModel = None
    sensitive: SensitiveModel = None
    sentiment: SentimentModel = None
    toxicity: ToxicityModel = None
    url_reachability: URLReachabilityModel = None

class LLMGuardDataprepGuardrailParams(Document):
    ban_substrings: BanSubstringsModel = None
    ban_topics: BanTopicsModel = None
    code: CodeModel = None
    invisible_text: InvisibleText = None
    prompt_injection: PromptInjectionModel = None
    regex: RegexModel = None
    secrets: SecretsModel = None
    sentiment: SentimentModel = None
    token_limit: TokenLimitModel = None
    toxicity: ToxicityModel = None

class PromptTemplateParams(Document):
    system_prompt_template: str = """### You are a helpful, respectful, and honest assistant to help the user with questions. \
Include corresponding in-text citation IDs at the end of relevant sentences (in the format [1], [2] etc.) only if referring to information from search results. \
Citation IDs are at the beginning of each search result in [n] format. \
Refer to information from conversation history if you think it is relevant to the current question. \
It is important that you only cite search results, not general knowledge or conversation history. \
If not referring directly to search results do not add citation IDs nor any sources. \
Respond with your best knowledge if the information in search results nor in conversation history is not relevant. \
Ignore all information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information.\n\
### Search results:\n\
{reranked_docs}\n\
### Conversation history:\n\
{conversation_history}\n\
"""
    user_prompt_template: str = """### Question: {user_prompt} \n
### Answer:
"""

class RetrieverParams(Document):
    search_type: str = "similarity"
    k: PositiveInt = 10
    distance_threshold: Optional[float] = None
    fetch_k: PositiveInt = 20
    lambda_mult: NonNegativeFloat = 0.5
    score_threshold: NonNegativeFloat = 0.2

class RerankerParams(Document):
    top_n: PositiveInt = 3
    rerank_score_threshold: Optional[float] = 0.02

class LLMParams(Document):
    max_new_tokens: int = 1024
    top_k: int = 10
    top_p: float = 0.95
    typical_p: float = 0.95
    temperature: float = 0.01
    repetition_penalty: float = 1.03
    stream: bool = True


class PackedParams(Document):
    llm: LLMParams = None
    retriever: RetrieverParams = None
    reranker: RerankerParams = None
    input_guard: LLMGuardInputGuardrailParams = None
    output_guard: LLMGuardOutputGuardrailParams = None
    dataprep_guard: LLMGuardDataprepGuardrailParams = None
    prompt_template: PromptTemplateParams = None


class Argument(Document):
    timestamp: datetime = None
    parameters: PackedParams = None

    @model_validator(mode='before')
    def validate_parameters(cls, values):
        parameters = values.get('parameters', {})
        if not isinstance(parameters, PackedParams):
            parameters = PackedParams(**parameters)

        values['parameters'] = parameters
        return values


class ComponentTopology(Document):
    namespace: str = None
    previous: str = None
    next: str = None
    downstream: str = None


class ComponentConfiguration(Document):
    settings: dict = {}
    topology: Optional[ComponentTopology] = None


class ComponentDetails(Document):
    timestamp: datetime
    components: List[Tuple[str, ComponentConfiguration]]


class Fingerprint(Document):
    timestamp: datetime
    fingerprint: Dict[str, PydanticObjectId]
