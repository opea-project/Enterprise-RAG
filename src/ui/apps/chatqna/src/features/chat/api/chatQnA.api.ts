// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createQnAApi, QnAApiConfig } from "@intel-enterprise-rag-ui/chat";

import { keycloakService } from "@/utils/auth";

const CHAT_QNA_API_CONFIG: QnAApiConfig = {
  postPromptEndpoint: "/api/v1/chatqna",
  reducerPath: "chatQnAApi",
};

export const chatQnAApi = createQnAApi(keycloakService, CHAT_QNA_API_CONFIG);

export const { usePostPromptMutation } = chatQnAApi;
