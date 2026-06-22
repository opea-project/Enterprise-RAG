// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceCard.scss";

import {
  LLMCard,
  LLMInputGuardCard,
  LLMOutputGuardCard,
  PostRetrieverQueryRequest,
  PromptTemplateCard,
  RerankerCard,
  RetrieverCard,
  RetrieverDebugDialogProps,
  validatePromptTemplateForm,
} from "@intel-enterprise-rag-ui/control-plane";
import { useDebug } from "@intel-enterprise-rag-ui/utils";

import {
  useChangeArgumentsMutation,
  usePostRetrieverQueryMutation,
} from "@/features/admin-panel/control-plane/api";
import {
  chatQnAGraphNodesSelector,
  chatQnAGraphSelectedServiceNodeSelector,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";
import { getChatQnAAppEnv } from "@/utils";
import { getErrorMessage } from "@/utils/api";
import { keycloakService } from "@/utils/auth";

const ServiceCard = () => {
  const [changeArguments] = useChangeArgumentsMutation();
  const selectedServiceNode = useAppSelector(
    chatQnAGraphSelectedServiceNodeSelector,
  );
  const chatQnAGraphNodes = useAppSelector(chatQnAGraphNodesSelector);
  const [postRetrieverQuery] = usePostRetrieverQueryMutation();
  const { isDebugEnabled } = useDebug();

  const rerankerNode = chatQnAGraphNodes.find((node) => node.id === "reranker");

  const handlePostRetrieverQuery: RetrieverDebugDialogProps["onPostRetrieverQuery"] =
    async (request: PostRetrieverQueryRequest) => {
      return await postRetrieverQuery(request);
    };

  const handleGetErrorMessage: RetrieverDebugDialogProps["onGetErrorMessage"] =
    (error: unknown, defaultMessage: string) => {
      return getErrorMessage(error, defaultMessage);
    };

  const isReadOnly =
    keycloakService.isMaintainerUser() && !keycloakService.isAdminUser();

  if (selectedServiceNode === null) {
    return <NoServiceSelectedCard />;
  }

  const { id, data } = selectedServiceNode;

  const cards: Record<string, JSX.Element> = {
    retriever: (
      <RetrieverCard
        data={data}
        changeArguments={changeArguments}
        isDebugEnabled={isDebugEnabled}
        rerankerArgs={rerankerNode?.data?.rerankerArgs}
        onPostRetrieverQuery={handlePostRetrieverQuery}
        onGetErrorMessage={handleGetErrorMessage}
        isReadOnly={isReadOnly}
        nerEnabled={getChatQnAAppEnv("NER_ENABLED") === "true"}
      />
    ),
    reranker: (
      <RerankerCard
        data={data}
        changeArguments={changeArguments}
        isReadOnly={isReadOnly}
      />
    ),
    prompt_template: (
      <PromptTemplateCard
        data={data}
        changeArguments={changeArguments}
        validatePromptTemplateForm={validatePromptTemplateForm}
        isReadOnly={isReadOnly}
      />
    ),
    input_guard: (
      <LLMInputGuardCard
        data={data}
        changeArguments={changeArguments}
        isReadOnly={isReadOnly}
      />
    ),
    llm: (
      <LLMCard
        data={data}
        changeArguments={changeArguments}
        isReadOnly={isReadOnly}
      />
    ),
    output_guard: (
      <LLMOutputGuardCard
        data={data}
        changeArguments={changeArguments}
        isReadOnly={isReadOnly}
      />
    ),
  };

  return cards[id] || null;
};

const NoServiceSelectedCard = () => (
  <div
    data-testid="no-service-selected-card"
    className="no-service-selected-card"
  >
    <p>Select service from the graph to see its details</p>
  </div>
);

export default ServiceCard;
