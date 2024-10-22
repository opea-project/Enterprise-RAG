// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatPage.scss";

import { useEffect } from "react";

import { ServicesParameters } from "@/api/models/systemFingerprint";
import ConversationFeed from "@/components/chat/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/chat/PromptInput/PromptInput";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  selectIsMessageStreamed,
  setPromptRequestParams,
} from "@/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ChatPage = () => {
  const dispatch = useAppDispatch();

  const isMessageStreamed = useAppSelector(selectIsMessageStreamed);

  useEffect(() => {
    const fetchPromptRequestParams = () => {
      SystemFingerprintService.appendArguments().then(
        (parameters: ServicesParameters) => {
          dispatch(setPromptRequestParams(parameters));
        },
      );
    };

    fetchPromptRequestParams();
    const intervalId = setInterval(() => {
      if (!isMessageStreamed) {
        fetchPromptRequestParams();
      }
    }, 10000);
    return () => {
      clearInterval(intervalId);
    };
  }, [isMessageStreamed]);

  return (
    <div className="chat-page">
      <ConversationFeed />
      <PromptInput />
    </div>
  );
};

export default ChatPage;
