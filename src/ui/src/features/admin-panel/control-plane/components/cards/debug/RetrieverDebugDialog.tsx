// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import Button from "@/components/ui/Button/Button";
import ConversationFeed from "@/components/ui/ConversationFeed/ConversationFeed";
import Dialog from "@/components/ui/Dialog/Dialog";
import PromptInput from "@/components/ui/PromptInput/PromptInput";
import { usePostRetrieverQueryMutation } from "@/features/admin-panel/control-plane/api";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentSelectInput from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ERROR_MESSAGES } from "@/features/admin-panel/control-plane/config/api";
import {
  RerankerArgs,
  rerankerArgumentsDefault,
  rerankerFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/reranker";
import {
  RetrieverArgs,
  retrieverArgumentsDefault,
  retrieverFormConfig,
  searchTypesArgsMap,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/retriever";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";
import { chatQnAGraphNodesSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import {
  filterInvalidRetrieverArguments,
  filterRetrieverFormData,
} from "@/features/admin-panel/control-plane/utils";
import { useAppSelector } from "@/store/hooks";
import { ConversationTurn } from "@/types";
import { getErrorMessage } from "@/utils/api";

const createCodeBlock = (text: string | object) => {
  let parsedText = text;
  if (typeof text === "string") {
    const trimmedText = text.trim();
    parsedText = JSON.parse(trimmedText);
  }
  const formattedText = JSON.stringify(parsedText, null, 2);
  return `\`\`\`\n${formattedText}\n\`\`\``;
};

const RetrieverDebugDialog = () => {
  const [postRetrieverQuery] = usePostRetrieverQueryMutation();

  const ref = useRef<HTMLDialogElement>(null);
  const handleClose = () => ref.current?.close();
  const showDialog = () => ref.current?.showModal();

  const trigger = (
    <Button size="sm" className="absolute right-4 top-4" onClick={showDialog}>
      Debug
    </Button>
  );

  const [isRerankerEnabled, setIsRerankerEnabled] = useState(false);
  const [conversationTurns, setConversationTurns] = useState<
    ConversationTurn[]
  >([]);
  const [query, setQuery] = useState("");

  const chatQnAGraphNodes = useAppSelector(chatQnAGraphNodesSelector);
  const retrieverNode = chatQnAGraphNodes.find(
    (node) => node.id === "retriever",
  );
  const retrieverArgs =
    retrieverNode?.data?.retrieverArgs ?? retrieverArgumentsDefault;

  const {
    argumentsForm: retrieverArgumentsForm,
    previousArgumentsValues: retrieverPreviousArgumentsValues,
    onArgumentValueChange: onRetrieverArgumentValueChange,
    onArgumentValidityChange: onRetrieverArgumentValidityChange,
  } = useServiceCard<RetrieverArgs>("retriever", retrieverArgs, {
    filterFormData: filterRetrieverFormData,
    filterInvalidArguments: filterInvalidRetrieverArguments,
  });

  const rerankerNode = chatQnAGraphNodes.find((node) => node.id === "reranker");
  const rerankerArgs =
    rerankerNode?.data?.rerankerArgs ?? rerankerArgumentsDefault;

  const {
    argumentsForm: rerankerArgumentsForm,
    previousArgumentsValues: rerankerPreviousArgumentsValues,
    onArgumentValueChange: onRerankerArgumentValueChange,
    onArgumentValidityChange: onRerankerArgumentValidityChange,
  } = useServiceCard<RerankerArgs>("reranker", rerankerArgs);

  const handleRerankerEnabledCheckboxChange: ChangeEventHandler<
    HTMLInputElement
  > = (event) => {
    setIsRerankerEnabled(event.target.checked);
  };

  const handleSubmitQuery = async (query: string) => {
    const newQueryRequest = {
      query,
      ...retrieverArgumentsForm,
      reranker: isRerankerEnabled,
      top_n: rerankerArgumentsForm.top_n,
      rerank_score_threshold: rerankerArgumentsForm.rerank_score_threshold,
    };

    setQuery("");

    const newConversationTurn: ConversationTurn = {
      id: uuidv4(),
      question: createCodeBlock(newQueryRequest),
      answer: "",
      error: null,
      isPending: true,
    };
    setConversationTurns((prevTurns) => [...prevTurns, newConversationTurn]);

    const { data, error } = await postRetrieverQuery(newQueryRequest);

    if (error) {
      const errorMessage = getErrorMessage(
        error,
        ERROR_MESSAGES.POST_RETRIEVER_QUERY,
      );
      setConversationTurns((prevTurns) => [
        ...prevTurns.slice(0, -1),
        { ...newConversationTurn, error: errorMessage, isPending: false },
      ]);
    } else {
      const responseData = data ? data : "";
      setConversationTurns((prevTurns) => [
        ...prevTurns.slice(0, -1),
        {
          ...newConversationTurn,
          answer: createCodeBlock(responseData),
          isPending: false,
        },
      ]);
    }
  };

  const handleQueryInputChange: ChangeEventHandler<HTMLTextAreaElement> = (
    event,
  ) => {
    setQuery(event.target.value);
  };

  return (
    <Dialog
      ref={ref}
      trigger={trigger}
      title="Retriever Debug"
      onClose={handleClose}
    >
      <div className="grid h-[calc(100vh-10rem)] grid-cols-[13rem_1fr] px-4 pt-4">
        <div>
          <RetrieverDebugParamsForm
            retrieverArgumentsForm={retrieverArgumentsForm}
            retrieverPreviousArgumentsValues={retrieverPreviousArgumentsValues}
            onRetrieverArgumentValueChange={onRetrieverArgumentValueChange}
            onRetrieverArgumentValidityChange={
              onRetrieverArgumentValidityChange
            }
            rerankerPreviousArgumentsValues={rerankerPreviousArgumentsValues}
            onRerankerArgumentValueChange={onRerankerArgumentValueChange}
            onRerankerArgumentValidityChange={onRerankerArgumentValidityChange}
            isRerankerEnabled={isRerankerEnabled}
            handleRerankerEnabledCheckboxChange={
              handleRerankerEnabledCheckboxChange
            }
          />
        </div>
        <div className="flex h-[calc(100vh-12rem)] flex-col text-sm">
          <div className="grid h-full grid-rows-[1fr_auto]">
            <RetrieverDebugChat
              conversationTurns={conversationTurns}
              query={query}
              handleQueryInputChange={handleQueryInputChange}
              handleSubmitQuery={handleSubmitQuery}
            />
          </div>
        </div>
      </div>
    </Dialog>
  );
};

interface RetrieverDebugParamsFormProps {
  retrieverArgumentsForm: RetrieverArgs;
  retrieverPreviousArgumentsValues: RetrieverArgs;
  onRetrieverArgumentValueChange: OnArgumentValueChangeHandler;
  onRetrieverArgumentValidityChange: OnArgumentValidityChangeHandler;
  rerankerPreviousArgumentsValues: RerankerArgs;
  onRerankerArgumentValueChange: OnArgumentValueChangeHandler;
  onRerankerArgumentValidityChange: OnArgumentValidityChangeHandler;
  isRerankerEnabled: boolean;
  handleRerankerEnabledCheckboxChange: ChangeEventHandler<HTMLInputElement>;
}

const RetrieverDebugParamsForm = ({
  retrieverArgumentsForm,
  retrieverPreviousArgumentsValues,
  onRetrieverArgumentValueChange,
  onRetrieverArgumentValidityChange,
  rerankerPreviousArgumentsValues,
  onRerankerArgumentValueChange,
  onRerankerArgumentValidityChange,
  isRerankerEnabled,
  handleRerankerEnabledCheckboxChange,
}: RetrieverDebugParamsFormProps) => {
  const visibleRerankerArgumentInputs = retrieverArgumentsForm?.search_type
    ? searchTypesArgsMap[retrieverArgumentsForm.search_type]
    : [];

  return (
    <>
      <p className="text-lg font-medium">Parameters</p>
      <p className="mb-2 mt-3">Retriever</p>
      <ServiceArgumentSelectInput
        {...retrieverFormConfig.search_type}
        initialValue={retrieverPreviousArgumentsValues.search_type}
        onArgumentValueChange={onRetrieverArgumentValueChange}
        readOnlyDisabled
      />
      {visibleRerankerArgumentInputs.includes(retrieverFormConfig.k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.k}
          initialValue={retrieverPreviousArgumentsValues.k}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
          readOnlyDisabled
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.distance_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.distance_threshold}
          initialValue={retrieverPreviousArgumentsValues.distance_threshold}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
          readOnlyDisabled
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.fetch_k.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.fetch_k}
          initialValue={retrieverPreviousArgumentsValues.fetch_k}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
          readOnlyDisabled
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.lambda_mult.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.lambda_mult}
          initialValue={retrieverPreviousArgumentsValues.lambda_mult}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
          readOnlyDisabled
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.score_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.score_threshold}
          initialValue={retrieverPreviousArgumentsValues.score_threshold}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
          readOnlyDisabled
        />
      )}
      <p className="mb-2 mt-3">Reranker</p>
      <div className="my-2 flex w-full items-center gap-2">
        <input
          type="checkbox"
          checked={isRerankerEnabled}
          name="reranker-enabled"
          id="reranker-enabled"
          onChange={handleRerankerEnabledCheckboxChange}
        />
        <label htmlFor="reranker-enabled" className="mb-0 text-xs">
          Enable Reranker
        </label>
      </div>
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.top_n}
        initialValue={rerankerPreviousArgumentsValues.top_n}
        onArgumentValueChange={onRerankerArgumentValueChange}
        onArgumentValidityChange={onRerankerArgumentValidityChange}
        readOnlyDisabled
      />
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.rerank_score_threshold}
        initialValue={rerankerPreviousArgumentsValues.rerank_score_threshold}
        onArgumentValueChange={onRerankerArgumentValueChange}
        onArgumentValidityChange={onRerankerArgumentValidityChange}
        readOnlyDisabled
      />
    </>
  );
};

interface RetrieverDebugChatProps {
  conversationTurns: ConversationTurn[];
  query: string;
  handleQueryInputChange: ChangeEventHandler<HTMLTextAreaElement>;
  handleSubmitQuery: (query: string) => void;
}

const RetrieverDebugChat = ({
  conversationTurns,
  query,
  handleQueryInputChange,
  handleSubmitQuery,
}: RetrieverDebugChatProps) => (
  <>
    <ConversationFeed conversationTurns={conversationTurns} />
    <PromptInput
      prompt={query}
      onChange={handleQueryInputChange}
      onSubmit={handleSubmitQuery}
    />
  </>
);

export default RetrieverDebugDialog;
