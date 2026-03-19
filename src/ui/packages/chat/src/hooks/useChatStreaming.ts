// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import type { Dispatch, UnknownAction } from "@reduxjs/toolkit";
import { useRef } from "react";

import {
  UseLazyGetChatByIdQuery,
  UseSaveChatMutation,
} from "@/api/chatHistory.api";
import { HTTP_ERRORS } from "@/api/config";
import { addChat } from "@/store/chatHistory.slice";
import { SourceDocumentType } from "@/types";
import { createChatTurnsFromHistory } from "@/utils";
import {
  isChatErrorResponse,
  isChatErrorResponseDataString,
} from "@/utils/api";

export interface UseChatStreamingConfig {
  dispatch: Dispatch<UnknownAction>;
  useSaveChatMutation: UseSaveChatMutation;
  useLazyGetChatByIdQuery: UseLazyGetChatByIdQuery;
  onNavigateToChat?: (chatId: string) => void;
}

export const useChatStreaming = (config: UseChatStreamingConfig) => {
  const {
    dispatch,
    useSaveChatMutation,
    useLazyGetChatByIdQuery,
    onNavigateToChat,
  } = config;

  const [saveChat] = useSaveChatMutation();
  const [getChatById] = useLazyGetChatByIdQuery();

  const currentAnswerRef = useRef("");
  const currentSourcesRef = useRef<SourceDocumentType[]>([]);

  const resetStreamingRefs = () => {
    currentAnswerRef.current = "";
    currentSourcesRef.current = [];
  };

  /**
   * Creates streaming callbacks that update refs and optionally a state updater
   */
  const createStreamingCallbacks = (
    onUpdateAnswer?: (answer: string) => void,
    onUpdateSources?: (sources: SourceDocumentType[]) => void,
  ) => {
    const onAnswerUpdate = (answer?: string) => {
      if (answer) {
        currentAnswerRef.current += answer;
        onUpdateAnswer?.(answer);
      }
    };

    const onSourcesUpdate = (sources: SourceDocumentType[]) => {
      currentSourcesRef.current = sources;
      onUpdateSources?.(sources);
    };

    return { onAnswerUpdate, onSourcesUpdate };
  };

  /**
   * Saves a chat and fetches it back to ensure data consistency
   * Returns the saved chat ID or undefined if save failed
   */
  const saveChatAndFetch = async (
    question: string,
    chatId?: string,
  ): Promise<string | undefined> => {
    const answer = currentAnswerRef.current;

    // Only save if we have a valid answer (not empty)
    if (!answer || answer.trim().length === 0) {
      return undefined;
    }

    try {
      const response = await saveChat({
        id: chatId,
        history: [
          {
            question: sanitizeString(question),
            answer,
            metadata: { reranked_docs: currentSourcesRef.current },
          },
        ],
      });

      if (response && "data" in response && response.data) {
        const { id } = response.data;

        // Fetch the chat from backend to ensure we have the latest data
        const chatData = await getChatById({ id }).unwrap();

        if (chatData) {
          const chatTurns = createChatTurnsFromHistory(chatData.history || []);

          dispatch(
            addChat({
              id,
              title:
                chatData.historyName || sanitizeString(question).slice(0, 50),
              turns: chatTurns,
              inputValue: "",
            }),
          );

          onNavigateToChat?.(id);

          return id;
        }
      }
    } catch (error) {
      console.error("Failed to save chat:", error);
    }

    return undefined;
  };

  /**
   * Handles streaming errors based on error type
   * Returns true if chat should be saved, false otherwise
   */
  const handleStreamingError = (
    error: unknown,
    onGuardrailsError?: (errorData: string) => void,
    onOtherError?: (errorData: string) => void,
  ): boolean => {
    if (
      error &&
      isChatErrorResponse(error) &&
      isChatErrorResponseDataString(error.data)
    ) {
      const errorData = error.data as string;

      if (error.status === HTTP_ERRORS.GUARDRAILS_ERROR.statusCode) {
        // Guardrails error - update answer and save
        currentAnswerRef.current += errorData;
        onGuardrailsError?.(errorData);
        return true; // Should save
      } else if (
        error.status === HTTP_ERRORS.CLIENT_CLOSED_REQUEST.statusCode
      ) {
        // Client closed request (abort) - save if we have an answer
        return currentAnswerRef.current.trim().length > 0;
      } else {
        // Other error - don't save
        onOtherError?.(errorData);
        return false;
      }
    }

    // No error or success - save
    return true;
  };

  return {
    currentAnswerRef,
    currentSourcesRef,
    resetStreamingRefs,
    createStreamingCallbacks,
    saveChatAndFetch,
    handleStreamingError,
  };
};
