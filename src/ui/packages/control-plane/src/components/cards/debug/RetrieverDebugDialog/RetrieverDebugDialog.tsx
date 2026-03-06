// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./RetrieverDebugDialog.scss";

import {
  ChatTurn,
  ConversationFeed,
  PromptInput,
} from "@intel-enterprise-rag-ui/chat";
import {
  Button,
  CheckboxInput,
  CheckboxInputChangeHandler,
  Dialog,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEventHandler, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { ServiceArgumentNumberInput } from "@/components/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import { ServiceArgumentSelectInput } from "@/components/ServiceArgumentSelectInput/ServiceArgumentSelectInput";
import { ServiceArgumentTextArea } from "@/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
import { ERROR_MESSAGES } from "@/configs/api";
import {
  RerankerArgs,
  rerankerArgumentsDefault,
  rerankerFormConfig,
} from "@/configs/services/reranker";
import {
  RetrieverArgs,
  retrieverArgumentsDefault,
  retrieverFormConfig,
  searchTypesArgsMap,
} from "@/configs/services/retriever";
import { useServiceCard } from "@/hooks/useServiceCard";
import { PostRetrieverQueryRequest } from "@/types/api/requests";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/index";
import {
  createFilterInvalidRetrieverArguments,
  createFilterRetrieverFormData,
} from "@/utils/card";

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

export interface RetrieverDebugDialogProps {
  retrieverArgs?: RetrieverArgs;
  rerankerArgs?: RerankerArgs;
  onPostRetrieverQuery: (
    request: PostRetrieverQueryRequest,
  ) => Promise<{ data?: unknown; error?: unknown }>;
  onGetErrorMessage: (error: unknown, defaultMessage: string) => string;
}

export const RetrieverDebugDialog = ({
  retrieverArgs: initialRetrieverArgs,
  rerankerArgs: initialRerankerArgs,
  onPostRetrieverQuery,
  onGetErrorMessage,
}: RetrieverDebugDialogProps) => {
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

  const retrieverArgs = initialRetrieverArgs ?? retrieverArgumentsDefault;
  const rerankerArgs = initialRerankerArgs ?? rerankerArgumentsDefault;

  const {
    argumentsForm: retrieverArgumentsForm,
    onArgumentValueChange: onRetrieverArgumentValueChange,
    onArgumentValidityChange: onRetrieverArgumentValidityChange,
  } = useServiceCard<RetrieverArgs>("retriever", retrieverArgs, {
    changeArguments: () => {}, // Debug mode - don't persist changes
    filterFns: {
      filterFormData: createFilterRetrieverFormData(searchTypesArgsMap),
      filterInvalidArguments:
        createFilterInvalidRetrieverArguments(searchTypesArgsMap),
    },
  });

  const {
    argumentsForm: rerankerArgumentsForm,
    onArgumentValueChange: onRerankerArgumentValueChange,
    onArgumentValidityChange: onRerankerArgumentValidityChange,
  } = useServiceCard<RerankerArgs>("reranker", rerankerArgs, {
    changeArguments: () => {}, // Debug mode - don't persist changes
  });

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

    const { data, error } = await onPostRetrieverQuery(newQueryRequest);

    if (error) {
      const errorMessage = onGetErrorMessage(
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
      data-testid="retriever-debug-dialog"
      trigger={
        <Button
          data-testid="retriever-debug-trigger-button"
          size="sm"
          className="retriever-debug-dialog__trigger-button"
        >
          Debug
        </Button>
      }
      title="Retriever Debug"
    >
      <div className="retriever-debug-dialog__container">
        <div className="retriever-debug-dialog__left-panel">
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
            <p className="retriever-debug-dialog__error-message">
              Invalid search_by parameter. It won&apos;t be included in the
              query.
            </p>
          )}
          <Button
            data-testid="format-json-button"
            size="sm"
            isDisabled={isFormatJSONButtonDisabled()}
            onPress={formatSearchByJSON}
            fullWidth
          >
            Format JSON
          </Button>
        </div>
        <div className="retriever-debug-dialog__right-panel">
          <div className="retriever-debug-dialog__chat-grid">
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
      <p className="retriever-debug-dialog__params-heading">Parameters</p>
      <p className="retriever-debug-dialog__section-heading">Retriever</p>
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
      <p className="retriever-debug-dialog__section-heading">Reranker</p>
      <CheckboxInput
        data-testid="reranker-enabled-checkbox"
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
    <ConversationFeed
      conversationTurns={conversationTurns}
      onFileDownload={() => {}}
    />
    <PromptInput
      prompt={query}
      onChange={handleQueryInputChange}
      onSubmit={handleSubmitQuery}
    />
  </>
);
