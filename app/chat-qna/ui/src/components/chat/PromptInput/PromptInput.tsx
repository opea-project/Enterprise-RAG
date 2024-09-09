// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import { fetchEventSource } from "@microsoft/fetch-event-source";
import { Button, TextField } from "@mui/material";
import { ChangeEvent, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import endpoints from "@/api/endpoints.json";
import {
  addMessage,
  selectIsMessageStreamed,
  setIsMessageStreamed,
  updateMessage,
} from "@/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const PromptInput = () => {
  const dispatch = useAppDispatch();
  const [prompt, setPrompt] = useState("");

  const isMessageStreamed = useAppSelector(selectIsMessageStreamed);

  const handlePromptInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target;
    setPrompt(value);
  };

  const handlePromptInputClear = () => {
    setPrompt("");
  };

  const handlePromptInputSubmit = async () => {
    const newUserMessage = { text: prompt, isUserMessage: true, id: uuidv4() };
    dispatch(addMessage(newUserMessage));

    dispatch(setIsMessageStreamed(true));

    const chatBotMessageId = uuidv4();
    const newMessage = {
      text: "",
      isUserMessage: false,
      id: chatBotMessageId,
    };
    dispatch(addMessage(newMessage));

    const requestBody = {
      docs: { text: prompt },
      parameters: {
        max_new_tokens: 256,
        do_sample: true,
        streaming: true,
      },
    };

    const url = window.location.origin + endpoints.chat;
    const ctrl = new AbortController();

    try {
      await fetchEventSource(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("token")}`,
        },
        body: JSON.stringify(requestBody),
        signal: ctrl.signal,
        openWhenHidden: true,
        onopen: async (response) => {
          if (response.ok) {
            return;
          } else if (
            response.status >= 400 &&
            response.status < 500 &&
            response.status !== 429
          ) {
            const error = await response.json();
            throw new Error(error);
          } else {
            console.error("Error during opening connection: ", response);
          }
        },
        onmessage: (event) => {
          if (![null, undefined, ""].includes(event.data)) {
            const regex = new RegExp(/'(.*?)'/);
            const matchedContent = event.data.match(regex);
            if (
              matchedContent &&
              Array.isArray(matchedContent) &&
              matchedContent.length > 1
            ) {
              const newChunk = matchedContent[1]
                .replace(/(\\n|<\/s>)/, "")
                .trimEnd();
              dispatch(
                updateMessage({ messageId: chatBotMessageId, chunk: newChunk }),
              );
            }
          }
        },
        onclose: () => {
          setPrompt("");
        },
      });
    } catch (error) {
      console.error("Error: ", error);
    } finally {
      dispatch(setIsMessageStreamed(false));
    }
  };

  const textFieldDisabled = isMessageStreamed;
  const actionsDisabled = prompt === "" || isMessageStreamed;

  return (
    <>
      <TextField
        id="prompt-input"
        value={prompt}
        onChange={handlePromptInputChange}
        disabled={textFieldDisabled}
        multiline
        rows={3}
        placeholder="Enter your prompt..."
      />
      <div className="prompt-input-actions">
        <Button disabled={actionsDisabled} onClick={handlePromptInputSubmit}>
          Submit
        </Button>
        <Button
          variant="outlined"
          disabled={actionsDisabled}
          onClick={handlePromptInputClear}
        >
          Clear
        </Button>
      </div>
    </>
  );
};

export default PromptInput;
