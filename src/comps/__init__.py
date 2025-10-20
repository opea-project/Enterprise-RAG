#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Statistics
from comps.cores.mega.base_statistics import register_statistics, statistics_dict

# Constants
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceRoleType, ServiceType

# Logger
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger, CustomLogger
from comps.cores.mega.micro_service import (
    MicroService,
    opea_microservices,
    register_microservice,
)

# Microservice
from comps.cores.mega.orchestrator import ServiceOrchestrator
from comps.cores.mega.orchestrator_with_yaml import ServiceOrchestratorWithYaml
# Document
from comps.cores.proto.docarray import (
    Audio2TextDoc,
    Base64ByteStrDoc,
    TextSplitterInput,
    DocPath,
    EmbedDoc,
    GeneratedDoc,
    GraphDoc,
    LLMParamsDoc,
    LLMPromptTemplate,
    LVMDoc,
    RAGASParams,
    RAGASScores,
    SearchedDoc,
    PrevQuestionDetails,
    PromptTemplateInput,
    TextDoc,
    TextCompressionInput,
    PromptCreate,
    PromptGet,
    PromptId,
    PromptOutput,
    TranslationInput,
    TextDocList,
    RerankedBaseDoc,
    RerankedFileDoc,
    RerankedLinkDoc
)

# Common
from comps.cores.common.component import OpeaComponent, OpeaComponentRegistry, OpeaComponentLoader

# Telemetry
from comps.cores.telemetry.opea_telemetry import opea_telemetry

# Utils
from comps.cores.utils.utils import sanitize_env
