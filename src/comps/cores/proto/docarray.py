# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import AudioDoc
from docarray.typing import AudioUrl
from pydantic import Field, conint, conlist, PositiveInt, NonNegativeFloat

class ComponentArgument(BaseDoc):
    name: str
    data: dict

class TopologyInfo:
    # will not keep forwarding to the downstream nodes in the black list
    # should be a pattern string
    downstream_black_list: Optional[list] = []

class PrevQuestionDetails(BaseDoc):
    question: str
    answer: str

class TextDoc(BaseDoc, TopologyInfo):
    text: str
    metadata: Optional[dict] = {}
    conversation_history: Optional[List[PrevQuestionDetails]] = None

class TextDocList(BaseDoc):
    docs: List[TextDoc]
    conversation_history: Optional[List[PrevQuestionDetails]] = None

class Base64ByteStrDoc(BaseDoc):
    byte_str: str

class DocPath(BaseDoc):
    path: str
    chunk_size: int = 1500
    chunk_overlap: int = 100
    process_table: bool = False
    table_strategy: str = "fast"

class EmbedDoc(BaseDoc):
    text: str
    embedding: conlist(float, min_length=0)
    search_type: str = "similarity"
    k: PositiveInt = 10
    distance_threshold: Optional[float] = None
    fetch_k: PositiveInt = 20
    lambda_mult: NonNegativeFloat = 0.5
    score_threshold: NonNegativeFloat = 0.2
    metadata: Optional[dict] = {}
    conversation_history: Optional[List[PrevQuestionDetails]] = None

class EmbedDocList(BaseDoc):
    docs: List[EmbedDoc]
    conversation_history: Optional[List[PrevQuestionDetails]] = None

class Audio2TextDoc(AudioDoc):
    url: Optional[AudioUrl] = Field(
        description="The path to the audio.",
        default=None,
    )
    model_name_or_path: Optional[str] = Field(
        description="The Whisper model name or path.",
        default="openai/whisper-small",
    )
    language: Optional[str] = Field(
        description="The language that Whisper prefer to detect.",
        default="auto",
    )


class DataPrepFile(BaseDoc):
    data64: str
    filename: str

class DataPrepInput(BaseDoc):
    files: List[DataPrepFile] = []
    links: List[str] = []
    chunk_size: Optional[Any] = None
    chunk_overlap: Optional[Any] = None
    process_table: Optional[Any] = None
    table_strategy: Optional[Any] = None
    max_new_tokens: Optional[PositiveInt] = None

class SearchedDoc(BaseDoc):
    retrieved_docs: DocList[TextDoc]
    user_prompt: str
    top_n: PositiveInt = 3
    rerank_score_threshold: Optional[float] = 0.02
    conversation_history: Optional[List[PrevQuestionDetails]] = None

    class Config:
        json_encoders = {np.ndarray: lambda x: x.tolist()}

class PromptTemplateInput(BaseDoc):
    data: Dict[str, Any]
    conversation_history: Optional[List[PrevQuestionDetails]] = None
    conversation_history_parse_type: str = "naive"
    system_prompt_template: Optional[str] = None
    user_prompt_template: Optional[str] = None

class AnonymizeModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    hidden_names: Optional[List[str]] = None
    allowed_names: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    preamble: Optional[str] = None
    regex_patterns: Optional[List[str]] = None
    use_faker: Optional[bool] = None
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None
    language: Optional[str] = None

class BanCodeModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None

class BanCompetitorsModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    competitors: List[str] = ["Competitor1", "Competitor2", "Competitor3"]
    model: Optional[str] = None
    threshold: Optional[float] = None
    redact: Optional[bool] = None

class BanSubstringsModel(BaseDoc):
    enabled: bool = False
    substrings: List[str] = ["backdoor", "malware", "virus"]
    match_type: Optional[str] = None
    case_sensitive: bool = False
    redact: Optional[bool] = None
    contains_all: Optional[bool] = None

class BanTopicsModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    topics: List[str] = ["violence","attack","war"]
    threshold: Optional[float] = None
    model: Optional[str] = None

class CodeModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    languages: List[str] = ["Java", "Python"]
    model: Optional[str] = None
    is_blocked: Optional[bool] = None
    threshold: Optional[float] = None

class GibberishModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class InvisibleText(BaseDoc):
    enabled: bool = False

class LanguageModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    valid_languages: List[str] = ["en", "es"]
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class PromptInjectionModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class RegexModel(BaseDoc):
    enabled: bool = False
    patterns: List[str] = ["Bearer [A-Za-z0-9-._~+/]+"]
    is_blocked: Optional[bool] = None
    match_type: Optional[str] = None
    redact: Optional[bool] = None

class SecretsModel(BaseDoc):
    enabled: bool = False
    redact_mode: Optional[str] = None

class SentimentModel(BaseDoc):
    enabled: bool = False
    threshold: Optional[float] = None
    lexicon: Optional[str] = None

class TokenLimitModel(BaseDoc):
    enabled: bool = False
    limit: Optional[int] = None
    encoding_name: Optional[str] = None
    model_name: Optional[str] = None

class ToxicityModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class BiasModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class DeanonymizeModel(BaseDoc):
    enabled: bool = False
    matching_strategy: Optional[str] = None

class JSONModel(BaseDoc):
    enabled: bool = False
    required_elements: Optional[int] = None
    repair: Optional[bool] = None

class LanguageSameModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None

class MaliciousURLsModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None

class NoRefusalModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None
    match_type: Optional[str] = None

class NoRefusalLightModel(BaseDoc):
    enabled: bool = False

class ReadingTimeModel(BaseDoc):
    enabled: bool = False
    max_time: float = 0.5
    truncate: Optional[bool] = None

class FactualConsistencyModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    minimum_score: Optional[float] = None

class RelevanceModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = None

class SensitiveModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    entity_types: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None
    redact: Optional[bool] = None
    recognizer_conf: Optional[str] = None
    threshold: Optional[float] = None

class URLReachabilityModel(BaseDoc):
    enabled: bool = False
    success_status_codes: Optional[List[int]] = None
    timeout: Optional[int] = None

class LLMGuardInputGuardrailParams(BaseDoc):
    anonymize: AnonymizeModel = AnonymizeModel()
    ban_code: BanCodeModel = BanCodeModel()
    ban_competitors: BanCompetitorsModel = BanCompetitorsModel()
    ban_substrings: BanSubstringsModel = BanSubstringsModel()
    ban_topics: BanTopicsModel = BanTopicsModel()
    code: CodeModel = CodeModel()
    gibberish: GibberishModel = GibberishModel()
    invisible_text: InvisibleText = InvisibleText()
    language: LanguageModel = LanguageModel()
    prompt_injection: PromptInjectionModel = PromptInjectionModel()
    regex: RegexModel = RegexModel()
    secrets: SecretsModel = SecretsModel()
    sentiment: SentimentModel = SentimentModel()
    token_limit: TokenLimitModel = TokenLimitModel()
    toxicity: ToxicityModel = ToxicityModel()

class LLMGuardOutputGuardrailParams(BaseDoc):
    ban_code: BanCodeModel = BanCodeModel()
    ban_competitors: BanCompetitorsModel = BanCompetitorsModel()
    ban_substrings: BanSubstringsModel = BanSubstringsModel()
    ban_topics: BanTopicsModel = BanTopicsModel()
    bias: BiasModel = BiasModel()
    code: CodeModel = CodeModel()
    deanonymize: DeanonymizeModel = DeanonymizeModel()
    json_scanner: JSONModel = JSONModel()
    language: LanguageModel = LanguageModel()
    language_same: LanguageSameModel = LanguageSameModel()
    malicious_urls: MaliciousURLsModel = MaliciousURLsModel()
    no_refusal: NoRefusalModel = NoRefusalModel()
    no_refusal_light: NoRefusalLightModel = NoRefusalLightModel()
    reading_time: ReadingTimeModel = ReadingTimeModel()
    factual_consistency: FactualConsistencyModel = FactualConsistencyModel()
    gibberish: GibberishModel = GibberishModel()
    regex: RegexModel = RegexModel()
    relevance: RelevanceModel = RelevanceModel()
    sensitive: SensitiveModel = SensitiveModel()
    sentiment: SentimentModel = SentimentModel()
    toxicity: ToxicityModel = ToxicityModel()
    url_reachability: URLReachabilityModel = URLReachabilityModel()
    anonymize_vault: Optional[List[Tuple]] = None # the only parameter not available in fingerprint. Used to tramsmit vault

class LLMPromptTemplate(BaseDoc):
    system: str
    user: str

class LLMParamsDoc(BaseDoc):
    messages: LLMPromptTemplate
    model: Optional[str] = None  # for openai and ollama
    max_new_tokens: PositiveInt = 1024
    top_k: PositiveInt = 10
    top_p: NonNegativeFloat = 0.95
    typical_p: NonNegativeFloat = 0.95
    temperature: NonNegativeFloat = 0.01
    repetition_penalty: NonNegativeFloat = 1.03
    streaming: bool = True
    input_guardrail_params: Optional[LLMGuardInputGuardrailParams] = None
    output_guardrail_params: Optional[LLMGuardOutputGuardrailParams] = None

class GeneratedDoc(BaseDoc):
    text: str
    prompt: str
    streaming: bool = True
    output_guardrail_params: Optional[LLMGuardOutputGuardrailParams] = None

class LLMParams(BaseDoc):
    max_new_tokens: PositiveInt = 1024
    top_k: PositiveInt = 10
    top_p: NonNegativeFloat = 0.95
    typical_p: NonNegativeFloat = 0.95
    temperature: NonNegativeFloat = 0.01
    repetition_penalty: NonNegativeFloat = 1.03
    streaming: bool = True


class RAGASParams(BaseDoc):
    questions: DocList[TextDoc]
    answers: DocList[TextDoc]
    docs: DocList[TextDoc]
    ground_truths: DocList[TextDoc]


class RAGASScores(BaseDoc):
    answer_relevancy: float
    faithfulness: float
    context_recallL: float
    context_precision: float


class GraphDoc(BaseDoc):
    text: str
    strtype: Optional[str] = Field(
        description="type of input query, can be 'query', 'cypher', 'rag'",
        default="query",
    )
    max_new_tokens: Optional[int] = Field(default=1024)
    rag_index_name: Optional[str] = Field(default="rag")
    rag_node_label: Optional[str] = Field(default="Task")
    rag_text_node_properties: Optional[list] = Field(default=["name", "description", "status"])
    rag_embedding_node_property: Optional[str] = Field(default="embedding")


class LVMDoc(BaseDoc):
    image: str
    prompt: str
    max_new_tokens: conint(ge=0, le=1024) = 512


class PromptCreate(BaseDoc):
    prompt_text: str
    filename: str

class PromptId(BaseDoc):
    prompt_id: str

class PromptGet(BaseDoc):
    filename: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_text: Optional[str] = None

class PromptOutput(BaseDoc):
    prompts: List[PromptGet]

class TranslationInput(BaseDoc):
    text: str
    target_language: str
