// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  Button,
  CheckboxInput,
  CheckboxInputChangeHandler,
  Dialog,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEventHandler, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import ConversationFeed from "@/components/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/PromptInput/PromptInput";
import { usePostRetrieverQueryMutation } from "@/features/admin-panel/control-plane/api";
import ServiceArgumentNumberInput from "@/features/admin-panel/control-plane/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentSelectInput from "@/features/admin-panel/control-plane/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import ServiceArgumentTextArea from "@/features/admin-panel/control-plane/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
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
import { PostRetrieverQueryRequest } from "@/features/admin-panel/control-plane/types/api";
import {
  filterInvalidRetrieverArguments,
  filterRetrieverFormData,
} from "@/features/admin-panel/control-plane/utils";
import { useAppSelector } from "@/store/hooks";
import { ChatTurn } from "@/types";
import { getErrorMessage } from "@/utils/api";

const initialSearchByParam = `{
    "bucket_name": "default",
    "object_name": ""
}`;

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

  const [isRerankerEnabled, setIsRerankerEnabled] = useState(false);
  const [conversationTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [query, setQuery] = useState("");
  const [searchByParam, setSearchByParam] = useState(initialSearchByParam);

  const handleSearchByParamChange: ChangeEventHandler<HTMLTextAreaElement> = (
    event,
  ) => {
    setSearchByParam(event.target.value);
  };

  const isSearchByJSONValid = () => {
    try {
      JSON.parse(searchByParam);
      return true;
    } catch {
      return false;
    }
  };

  const isFormatJSONButtonDisabled = () => {
    try {
      const parsed = JSON.parse(searchByParam);
      const formatted = JSON.stringify(parsed, null, 4);
      return searchByParam.trim() === formatted.trim();
    } catch {
      return true;
    }
  };

  const formatSearchByJSON = () => {
    setSearchByParam((prevValue) =>
      JSON.stringify(JSON.parse(prevValue), null, 4),
    );
  };

  const chatQnAGraphNodes = useAppSelector(chatQnAGraphNodesSelector);
  const retrieverNode = chatQnAGraphNodes.find(
    (node) => node.id === "retriever",
  );
  const retrieverArgs =
    retrieverNode?.data?.retrieverArgs ?? retrieverArgumentsDefault;

  const {
    argumentsForm: retrieverArgumentsForm,
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
    onArgumentValueChange: onRerankerArgumentValueChange,
    onArgumentValidityChange: onRerankerArgumentValidityChange,
  } = useServiceCard<RerankerArgs>("reranker", rerankerArgs);

  const handleRerankerEnabledCheckboxChange: CheckboxInputChangeHandler = (
    isSelected,
  ) => {
    setIsRerankerEnabled(isSelected);
  };

  const handleSubmitQuery = async (query: string) => {
    const newQueryRequest: PostRetrieverQueryRequest = {
      query,
      ...retrieverArgumentsForm,
      reranker: isRerankerEnabled,
      top_n: rerankerArgumentsForm.top_n,
      rerank_score_threshold: rerankerArgumentsForm.rerank_score_threshold,
    };

    if (isSearchByJSONValid()) {
      newQueryRequest.search_by = searchByParam
        ? JSON.parse(searchByParam)
        : undefined;
    }

    setQuery("");

    const newChatTurn: ChatTurn = {
      id: uuidv4(),
      question: createCodeBlock(newQueryRequest),
      answer: "",
      error: null,
      isPending: true,
    };
    setChatTurns((prevTurns) => [...prevTurns, newChatTurn]);

    const { data, error } = await postRetrieverQuery(newQueryRequest);

    if (error) {
      const errorMessage = getErrorMessage(
        error,
        ERROR_MESSAGES.POST_RETRIEVER_QUERY,
      );
      setChatTurns((prevTurns) => [
        ...prevTurns.slice(0, -1),
        { ...newChatTurn, error: errorMessage, isPending: false },
      ]);
    } else {
      const responseData = data ? data : "";
      setChatTurns((prevTurns) => [
        ...prevTurns.slice(0, -1),
        {
          ...newChatTurn,
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
      trigger={
        <Button size="sm" className="absolute right-4 top-4">
          Debug
        </Button>
      }
      title="Retriever Debug"
    >
      <div className="grid grid-cols-[14rem_1fr] px-3 py-3">
        <div className="h-[calc(100vh_-_12rem)] overflow-y-auto pl-1 pr-3 [scrollbar-gutter:stable]">
          <RetrieverDebugParamsForm
            retrieverArgumentsForm={retrieverArgumentsForm}
            rerankerArgumentsForm={rerankerArgumentsForm}
            isRerankerEnabled={isRerankerEnabled}
            onRetrieverArgumentValueChange={onRetrieverArgumentValueChange}
            onRetrieverArgumentValidityChange={
              onRetrieverArgumentValidityChange
            }
            onRerankerArgumentValueChange={onRerankerArgumentValueChange}
            onRerankerArgumentValidityChange={onRerankerArgumentValidityChange}
            onRerankerEnabledCheckboxChange={
              handleRerankerEnabledCheckboxChange
            }
          />
          <ServiceArgumentTextArea
            value={searchByParam}
            placeholder="Enter search_by parameters in JSON format"
            isInvalid={!isSearchByJSONValid()}
            rows={5}
            titleCaseLabel={false}
            inputConfig={{
              name: "search_by",
              tooltipText: "Search by parameters in JSON format",
            }}
            onChange={handleSearchByParamChange}
          />
          {!isSearchByJSONValid() && (
            <p className="error mb-2 text-xs italic">
              Invalid search_by parameter. It won&apos;t be included in the
              query.
            </p>
          )}
          <Button
            size="sm"
            isDisabled={isFormatJSONButtonDisabled()}
            onPress={formatSearchByJSON}
            fullWidth
          >
            Format JSON
          </Button>
        </div>
        <div className="flex h-[calc(100vh_-_12rem)] flex-col text-sm">
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
  rerankerArgumentsForm: RerankerArgs;
  isRerankerEnabled: boolean;
  onRetrieverArgumentValueChange: OnArgumentValueChangeHandler;
  onRetrieverArgumentValidityChange: OnArgumentValidityChangeHandler;
  onRerankerArgumentValueChange: OnArgumentValueChangeHandler;
  onRerankerArgumentValidityChange: OnArgumentValidityChangeHandler;
  onRerankerEnabledCheckboxChange: CheckboxInputChangeHandler;
}

const RetrieverDebugParamsForm = ({
  retrieverArgumentsForm,
  rerankerArgumentsForm,
  onRetrieverArgumentValueChange,
  onRetrieverArgumentValidityChange,
  onRerankerArgumentValueChange,
  onRerankerArgumentValidityChange,
  isRerankerEnabled,
  onRerankerEnabledCheckboxChange,
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
        value={retrieverArgumentsForm.search_type}
        onArgumentValueChange={onRetrieverArgumentValueChange}
      />
      {visibleRerankerArgumentInputs.includes(retrieverFormConfig.k.name) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.k}
          value={retrieverArgumentsForm.k}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.distance_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.distance_threshold}
          value={retrieverArgumentsForm.distance_threshold}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.fetch_k.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.fetch_k}
          value={retrieverArgumentsForm.fetch_k}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.lambda_mult.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.lambda_mult}
          value={retrieverArgumentsForm.lambda_mult}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
        />
      )}
      {visibleRerankerArgumentInputs.includes(
        retrieverFormConfig.score_threshold.name,
      ) && (
        <ServiceArgumentNumberInput
          {...retrieverFormConfig.score_threshold}
          value={retrieverArgumentsForm.score_threshold}
          onArgumentValueChange={onRetrieverArgumentValueChange}
          onArgumentValidityChange={onRetrieverArgumentValidityChange}
        />
      )}
      <p className="mb-2 mt-3">Reranker</p>
      <CheckboxInput
        label="Enable Reranker"
        size="sm"
        name="reranker-enabled"
        isSelected={isRerankerEnabled}
        onChange={onRerankerEnabledCheckboxChange}
      />
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.top_n}
        value={rerankerArgumentsForm.top_n}
        onArgumentValueChange={onRerankerArgumentValueChange}
        onArgumentValidityChange={onRerankerArgumentValidityChange}
      />
      <ServiceArgumentNumberInput
        {...rerankerFormConfig.rerank_score_threshold}
        value={rerankerArgumentsForm.rerank_score_threshold}
        onArgumentValueChange={onRerankerArgumentValueChange}
        onArgumentValidityChange={onRerankerArgumentValidityChange}
      />
    </>
  );
};

interface RetrieverDebugChatProps {
  conversationTurns: ChatTurn[];
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
