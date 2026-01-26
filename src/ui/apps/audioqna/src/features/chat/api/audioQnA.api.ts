// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createQnAApi, QnAApiConfig } from "@intel-enterprise-rag-ui/chat";

import { keycloakService } from "@/utils/auth";

const AUDIO_QNA_API_CONFIG: QnAApiConfig = {
  postPromptEndpoint: "/api/v1/audioqna",
  reducerPath: "audioQnAApi",
};

export const audioQnAApi = createQnAApi(keycloakService, AUDIO_QNA_API_CONFIG);

export const { usePostPromptMutation } = audioQnAApi;
