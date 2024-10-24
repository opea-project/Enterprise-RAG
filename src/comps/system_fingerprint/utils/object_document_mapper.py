# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pydantic import model_validator
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from beanie import Document, PydanticObjectId


class AnonymizeModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    hidden_names: Optional[List[str]] = None
    allowed_names: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    preamble: Optional[str] = None
    regex_patterns: Optional[List[str]] = None
    use_faker: Optional[bool] = None
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None
    language: Optional[str] = None


class BanCodeModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None


class BanCompetitorsModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    competitors: List[str] = ["Competitor1", "Competitor2", "Competitor3"]
    model: Optional[str] = None
    threshold: Optional[float] = None
    redact: Optional[bool] = None


class BanSubstringsModel(Document):
    enabled: bool = False
    substrings: List[str] = ["backdoor", "malware", "virus"]
    match_type: Optional[str] = None
    case_sensitive: bool = False
    redact: Optional[bool] = None
    contains_all: Optional[bool] = None


class BanTopicsModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    topics: List[str] = ["violence", "attack", "war"]
    threshold: Optional[float] = None
    model: Optional[str] = None


class CodeModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    languages: List[str] = ["Java", "Python"]
    model: Optional[str] = None
    is_blocked: Optional[bool] = None
    threshold: Optional[float] = None


class GibberishModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class InvisibleText(Document):
    enabled: bool = False


class LanguageModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    valid_languages: List[str] = ["en", "es"]
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class PromptInjectionModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class RegexModel(Document):
    enabled: bool = False
    patterns: List[str] = ["Bearer [A-Za-z0-9-._~+/]+"]
    is_blocked: Optional[bool] = None
    match_type: Optional[str] = None
    redact: Optional[bool] = None


class SecretsModel(Document):
    enabled: bool = False
    redact_mode: Optional[str] = None


class SentimentModel(Document):
    enabled: bool = False
    threshold: Optional[float] = None
    lexicon: Optional[str] = None


class TokenLimitModel(Document):
    enabled: bool = False
    limit: Optional[int] = None
    encoding_name: Optional[str] = None
    model_name: Optional[str] = None


class ToxicityModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class BiasModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class DeanonymizeModel(Document):
    enabled: bool = False
    matching_strategy: Optional[str] = None


class JSONModel(Document):
    enabled: bool = False
    required_elements: Optional[int] = None
    repair: Optional[bool] = None


class LanguageSameModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None


class MaliciousURLsModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None


class NoRefusalModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None


class NoRefusalLightModel(Document):
    enabled: bool = False
    substrings: Optional[List[str]] = None
    match_type: Optional[str] = None
    case_sensitive: bool = False
    redact: Optional[bool] = None
    contains_all: Optional[bool] = None


class ReadingTimeModel(Document):
    enabled: bool = False
    max_time: float = 0.5
    truncate: Optional[bool] = None


class FactualConsistencyModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    minimum_score: Optional[float] = None


class RelevanceModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    model: Optional[str] = None
    threshold: Optional[float] = None


class SensitiveModel(Document):
    enabled: bool = False
    use_onnx: bool = True
    entity_types: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None
    redact: Optional[bool] = None
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None


class URLReachabilityModel(Document):
    enabled: bool = False
    success_status_codes: Optional[List[int]] = None
    timeout: Optional[int] = None


class LLMGuardInputGuardrailParams(Document):
    anonymize: AnonymizeModel = None
    ban_code: BanCodeModel = None
    ban_competitors: BanCompetitorsModel = None
    ban_substrings: BanSubstringsModel = None
    ban_topics: BanTopicsModel = None
    code: CodeModel = None
    gibberish: GibberishModel = None
    invisible_text: InvisibleText = None
    language: LanguageModel = None
    prompt_injection: PromptInjectionModel = None
    regex: RegexModel = None
    secrets: SecretsModel = None
    sentiment: SentimentModel = None
    token_limit: TokenLimitModel = None
    toxicity: ToxicityModel = None


class LLMGuardOutputGuardrailParams(Document):
    ban_competitors: BanCompetitorsModel = None
    ban_substrings: BanSubstringsModel = None
    ban_topics: BanTopicsModel = None
    bias: BiasModel = None
    code: CodeModel = None
    deanonymize: DeanonymizeModel = None
    json_scanner: JSONModel = None
    language: LanguageModel = None
    language_same: LanguageSameModel = None
    malicious_urls: MaliciousURLsModel = None
    no_refusal: NoRefusalModel = None
    no_refusal_light: NoRefusalLightModel = None
    reading_time: ReadingTimeModel = None
    factual_consistency: FactualConsistencyModel = None
    gibberish: GibberishModel = None
    regex: RegexModel = None
    relevance: RelevanceModel = None
    sensitive: SensitiveModel = None
    sentiment: SentimentModel = None
    toxicity: ToxicityModel = None
    url_reachability: URLReachabilityModel = None
    output_guard_streaming: bool = True


class RerankerParams(Document):
    search_type: str = "similarity"
    k: int = 4
    distance_threshold: Optional[float] = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    score_threshold: float = 0.2


class LLMParams(Document):
    max_new_tokens: int = 1024
    top_k: int = 10
    top_p: float = 0.95
    typical_p: float = 0.95
    temperature: float = 0.01
    repetition_penalty: float = 1.03
    streaming: bool = False


class PackedParams(Document):
    llm: LLMParams = None
    reranker: RerankerParams = None
    input_guard: LLMGuardInputGuardrailParams = None
    output_guard: LLMGuardOutputGuardrailParams = None


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
