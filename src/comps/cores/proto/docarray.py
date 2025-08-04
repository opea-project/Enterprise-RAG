# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List, Dict, Optional, Tuple, Any

import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import AudioDoc
from docarray.typing import AudioUrl
from pydantic import BaseModel, Field, conint, conlist, PositiveInt, NonNegativeFloat

class ComponentArgument(BaseDoc):
    name: str
    data: dict

class TopologyInfo:
    # will not keep forwarding to the downstream nodes in the black list
    # should be a pattern string
    downstream_black_list: Optional[list] = []

class ChatMessage(BaseModel):
    question: str
    answer: str

class ChatHistory(BaseModel):
    id: Optional[str] = None
    history: List[ChatMessage]

class ChatHistoryName(BaseModel):
    id: str
    history_name: str

class PrevQuestionDetails(BaseDoc):
    question: str
    answer: str

class TextDoc(BaseDoc, TopologyInfo):
    text: str
    metadata: Optional[dict] = {}
    history_id: Optional[str] = None

    def to_reranked_doc(self):
        if self.metadata and 'url' in self.metadata:
            return RerankedLinkDoc(
                text=self.text,
                url=self.metadata.get('url'),
                vector_distance=self.metadata.get('vector_distance', 1.0),
                reranker_score=self.metadata.get('reranker_score', 0.0),
                citation_id=self.metadata.get('citation_id', 0)
            )
            
        if self.metadata and 'bucket_name' in self.metadata and 'object_name' in self.metadata:
            return RerankedFileDoc(
                text=self.text,
                bucket_name=self.metadata.get('bucket_name'),
                object_name=self.metadata.get('object_name'),
                vector_distance=self.metadata.get('vector_distance', 1.0),
                reranker_score=self.metadata.get('reranker_score', 0.0),
                citation_id=self.metadata.get('citation_id', 0)
            )
        raise ValueError("TextDoc must have either 'url' or both 'bucket_name' and 'object_name' in metadata to convert to RerankedDoc.")

class RerankedBaseDoc(BaseDoc):
    vector_distance: float = 1.0 # max far away
    reranker_score: float = 0.0 # lowest score
    citation_id: int = 0

class RerankedFileDoc(RerankedBaseDoc):
    type: str = "file"
    bucket_name: str
    object_name: str

class RerankedLinkDoc(RerankedBaseDoc):
    type: str = "link"
    url: str

class Base64ByteStrDoc(BaseDoc):
    byte_str: str

class DocPath(BaseDoc):
    path: str
    chunk_size: int = 1500
    chunk_overlap: int = 100

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
    history_id: Optional[str] = None

class EmbedDocList(BaseDoc):
    docs: List[EmbedDoc]
    history_id: Optional[str] = None

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

class HierarchicalDataPrepInput(BaseDoc):
    files: List[DataPrepFile] = []
    links: List[str] = []
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    max_new_tokens: Optional[PositiveInt] = None

class TextCompressionTechnique(BaseDoc):
    name: str
    parameters: Optional[Dict[str, Any]] = None

class TextCompressionInput(BaseDoc):
    loaded_docs: List[TextDoc]
    compression_techniques: Optional[List[TextCompressionTechnique]] = None

class TextSplitterInput(BaseDoc):
    loaded_docs: List[TextDoc]
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    use_semantic_chunking: Optional[bool] = None
    semantic_chunk_params: Optional[Dict[str, Any]] = None

class SearchedDoc(BaseDoc):
    retrieved_docs: DocList[TextDoc]
    user_prompt: str
    sibling_docs: Optional[Dict[str, DocList[TextDoc]]] = None
    top_n: PositiveInt = 3
    rerank_score_threshold: Optional[float] = 0.02
    history_id: Optional[str] = None

    class Config:
        json_encoders = {np.ndarray: lambda x: x.tolist()}

class PromptTemplateInput(BaseDoc):
    data: Dict[str, Any]
    history_id: Optional[str] = None
    chat_history_parse_type: str = "naive"
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

class BanSubstringsModel(BaseDoc):
    enabled: bool = False
    substrings: List[str] = ["backdoor", "malware", "virus"]
    match_type: Optional[str] = "str"
    case_sensitive: bool = False
    redact: Optional[bool] = None
    contains_all: Optional[bool] = None

class BanTopicsModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    topics: List[str] = ["violence","attack","war"]
    threshold: Optional[float] = 0.6
    model: Optional[str] = None

class CodeModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    languages: List[str] = ["Java", "Python"]
    model: Optional[str] = None
    is_blocked: Optional[bool] = None
    threshold: Optional[float] = 0.5

class InvisibleText(BaseDoc):
    enabled: bool = False

class PromptInjectionModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = 0.92
    match_type: Optional[str] = "full"

class RegexModel(BaseDoc):
    enabled: bool = False
    patterns: List[str] = ["Bearer [A-Za-z0-9-._~+/]+"]
    is_blocked: Optional[bool] = None
    match_type: Optional[str] = "all"
    redact: Optional[bool] = None

class SecretsModel(BaseDoc):
    enabled: bool = False
    redact_mode: Optional[str] = "all"

class SentimentModel(BaseDoc):
    enabled: bool = False
    threshold: Optional[float] = -0.3
    lexicon: Optional[str] = None

class TokenLimitModel(BaseDoc):
    enabled: bool = False
    limit: Optional[int] = 4096
    encoding_name: Optional[str] = "cl100k_base"
    model_name: Optional[str] = None

class ToxicityModel(BaseDoc):
    enabled: bool = False
    use_onnx: bool = False
    model: Optional[str] = None
    threshold: Optional[float] = 0.5
    match_type: Optional[str] = "full"

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
    ban_substrings: BanSubstringsModel = BanSubstringsModel()
    ban_topics: BanTopicsModel = BanTopicsModel()
    code: CodeModel = CodeModel()
    invisible_text: InvisibleText = InvisibleText()
    prompt_injection: PromptInjectionModel = PromptInjectionModel()
    regex: RegexModel = RegexModel()
    secrets: SecretsModel = SecretsModel()
    sentiment: SentimentModel = SentimentModel()
    token_limit: TokenLimitModel = TokenLimitModel()
    toxicity: ToxicityModel = ToxicityModel()

class LLMGuardOutputGuardrailParams(BaseDoc):
    ban_substrings: BanSubstringsModel = BanSubstringsModel()
    ban_topics: BanTopicsModel = BanTopicsModel()
    bias: BiasModel = BiasModel()
    code: CodeModel = CodeModel()
    deanonymize: DeanonymizeModel = DeanonymizeModel()
    json_scanner: JSONModel = JSONModel()
    malicious_urls: MaliciousURLsModel = MaliciousURLsModel()
    no_refusal: NoRefusalModel = NoRefusalModel()
    no_refusal_light: NoRefusalLightModel = NoRefusalLightModel()
    reading_time: ReadingTimeModel = ReadingTimeModel()
    factual_consistency: FactualConsistencyModel = FactualConsistencyModel()
    regex: RegexModel = RegexModel()
    relevance: RelevanceModel = RelevanceModel()
    sensitive: SensitiveModel = SensitiveModel()
    sentiment: SentimentModel = SentimentModel()
    toxicity: ToxicityModel = ToxicityModel()
    url_reachability: URLReachabilityModel = URLReachabilityModel()
    anonymize_vault: Optional[List[Tuple]] = None # the only parameter not available in fingerprint. Used to tramsmit vault

class LLMGuardDataprepGuardrailParams(BaseDoc):
    ban_substrings: BanSubstringsModel = BanSubstringsModel()
    ban_topics: BanTopicsModel = BanTopicsModel()
    code: CodeModel = CodeModel()
    invisible_text: InvisibleText = InvisibleText()
    prompt_injection: PromptInjectionModel = PromptInjectionModel()
    regex: RegexModel = RegexModel()
    secrets: SecretsModel = SecretsModel()
    sentiment: SentimentModel = SentimentModel()
    token_limit: TokenLimitModel = TokenLimitModel()
    toxicity: ToxicityModel = ToxicityModel()

class TextDocList(BaseDoc):
    docs: List[TextDoc]
    history_id: Optional[str] = None
    dataprep_guardrail_params: Optional[LLMGuardDataprepGuardrailParams] = None

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
    data: Optional[Dict[str, Any]] = None

class GeneratedDoc(BaseDoc):
    text: str
    prompt: str
    streaming: bool = True
    output_guardrail_params: Optional[LLMGuardOutputGuardrailParams] = None
    data: Optional[Dict[str, Any]] = None

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
