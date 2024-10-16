// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ChatPage.scss";

import { useEffect } from "react";

import { ServicesParameters } from "@/api/models/system-fingerprint/appendArguments";
import ConversationFeed from "@/components/chat/ConversationFeed/ConversationFeed";
import PromptInput from "@/components/chat/PromptInput/PromptInput";
import SystemFingerprintService from "@/services/systemFingerprintService";
import { setPromptRequestParams } from "@/store/conversationFeed.slice";
import { useAppDispatch } from "@/store/hooks";

const ChatPage = () => {
  const dispatch = useAppDispatch();

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
      fetchPromptRequestParams();
    }, 10000);
    return () => {
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="chat-page">
      <ConversationFeed />
      <PromptInput />
    </div>
  );
};

export default ChatPage;
