# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from enum import Enum


class ServiceRoleType(Enum):
    """The enum of a service role."""

    MICROSERVICE = 0
    MEGASERVICE = 1


class ServiceType(Enum):
    """The enum of a service type."""

    GATEWAY = 0
    EMBEDDING = 1
    RETRIEVER = 2
    RERANK = 3
    LLM = 4
    ASR = 5
    TTS = 6
    GUARDRAIL = 7
    VECTORSTORE = 8
    DATAPREP = 9
    UNDEFINED = 10
    RAGAS = 11
    LVM = 12
    KNOWLEDGE_GRAPH = 13
    WEB_RETRIEVER = 14
    LLM_GUARD_INPUT_SCANNER = 15
    LLM_GUARD_OUTPUT_SCANNER = 16
    INGESTION = 17
    LANGUAGE_DETECTION = 18
    PROMPT_TEMPLATE = 19
    LLM_GUARD_DATAPREP_SCANNER = 20
    HIERARCHICAL_DATAPREP = 21
    TEXT_EXTRACTOR = 22
    TEXT_COMPRESSION = 23
    TEXT_SPLITTER = 24
    CHAT_HISTORY = 25
    # GenAIComps exclusive
    IMAGE2VIDEO = 26
    TEXT2IMAGE = 27
    ANIMATION = 28
    IMAGE2IMAGE = 29
    TEXT2SQL = 30
    TEXT2GRAPH = 31
    TEXT2CYPHER = 32
    TEXT2KG = 33
    STRUCT2GRAPH = 34
    # End GenAIComps exclusive
    DOC_SUMMARY = 35
    LATE_CHUNKING = 36
    NAMESPACE_STATUS_WATCHER = 37


class MegaServiceEndpoint(Enum):
    """The enum of an MegaService endpoint."""

    # OPEA Exclusive
    CHAT_QNA = "/v1/chatqna"
    AUDIO_QNA = "/v1/audioqna"
    VISUAL_QNA = "/v1/visualqna"
    CODE_GEN = "/v1/codegen"
    CODE_TRANS = "/v1/codetrans"
    DOC_SUMMARY = "/v1/docsum"
    SEARCH_QNA = "/v1/searchqna"
    TRANSLATION = "/v1/translation"
    LANGUAGE_DETECTION = "/v1/language_detection"
    FAQ_GEN = "/v1/faqgen"
    # GenAIComps exclusive
    AVATAR_CHATBOT = "/v1/avatarchatbot"
    GRAPH_RAG = "/v1/graphrag"
    HYBRID_RAG = "/v1/hybridrag"
    RETRIEVALTOOL = "/v1/retrievaltool"
    MULTIMODAL_QNA = "/v1/multimodalqna"
    VIDEO_RAG_QNA = "/v1/videoqna"
    # Follow OPENAI
    EMBEDDINGS = "/v1/embeddings"
    TTS = "/v1/audio/speech"
    ASR = "/v1/audio/transcriptions"
    CHAT = "/v1/chat/completions"
    RETRIEVAL = "/v1/retrieval"
    RERANKING = "/v1/reranking"
    PROMPT_TEMPLATE = "/v1/prompt_template"
    GUARDRAILS = "/v1/guardrails"
    RAGAS = "/v1/ragas"
    GRAPHS = "/v1/graphs"
    LLM_GUARD_INPUT_SCANNER = "/v1/llmguardinput"
    LLM_GUARD_OUTPUT_SCANNER = "/v1/llmguardoutput"
    INGEST = "/v1/ingestion"
    DATAPREP = '/v1/dataprep'
    PROMPT_REGISTRY = '/v1/prompt_registry'
    SYSTEM_FINGERPRINT = '/v1/system_fingerprint'
    LLM_GUARD_DATAPREP_SCANNER = "/v1/llmguarddataprep"
    HIERARCHICAL_DATAPREP = "/v1/hierarchical_dataprep"
    TEXT_EXTRACTOR = "/v1/text_extractor"
    TEXT_COMPRESSION = "/v1/text_compression"
    TEXT_SPLITTER = "/v1/text_splitter"
    CHAT_HISTORY = "/v1/chat_history"
    LATE_CHUNKING = "/v1/late_chunking"

    # COMMON
    LIST_SERVICE = "/v1/list_service"
    LIST_PARAMETERS = "/v1/list_parameters"

    def __str__(self):
        return self.value


class MicroServiceEndpoint(Enum):
    """The enum of an MicroService endpoint."""

    EMBEDDINGS = "/v1/microservice/embeddings"
    TTS = "/v1/microservice/tts"
    ASR = "/v1/microservice/asr"
    CHAT = "/v1/microservice/chat"
    RETRIEVAL = "/v1/microservice/retrieval"
    RERANKING = "/v1/microservice/reranking"
    GUARDRAILS = "/v1/microservice/guardrails"
    RAGAS = "/v1/microservice/ragas"

    def __str__(self):
        return self.value
