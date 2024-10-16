// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import { fetchEventSource } from "@microsoft/fetch-event-source";
import classNames from "classnames";
import {
  ChangeEvent,
  KeyboardEventHandler,
  useEffect,
  useRef,
  useState,
} from "react";
import { BsHurricane, BsSendFill } from "react-icons/bs";
import { v4 as uuidv4 } from "uuid";

import endpoints from "@/api/endpoints.json";
import {
  addMessage,
  selectIsMessageStreamed,
  selectPromptRequestParams,
  setIsMessageStreamed,
  updateMessage,
} from "@/store/conversationFeed.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const PromptInput = () => {
  const dispatch = useAppDispatch();
  const promptInputRef = useRef<HTMLTextAreaElement>(null);
  const [prompt, setPrompt] = useState("");
  const [textAreaRows, setTextAreaRows] = useState(1);

  const isMessageStreamed = useAppSelector(selectIsMessageStreamed);
  const promptRequestParams = useAppSelector(selectPromptRequestParams);

  useEffect(() => {
    promptInputRef.current!.focus();
  }, []);

  useEffect(() => {
    if (!isMessageStreamed) {
      promptInputRef.current!.focus();
    }
  }, [isMessageStreamed]);

  const handlePromptInputChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const input = event.target;
    setPrompt(input.value);

    input.style.height = "auto";

    const verticalPadding = 16;
    const lineHeight = 24;
    const textareaScrollHeight = input.scrollHeight - verticalPadding;
    const newRows = Math.max(Math.ceil(textareaScrollHeight / lineHeight), 1);
    setTextAreaRows(newRows);

    input.style.height = "";
  };

  useEffect(() => {
    if (prompt === "") {
      setTextAreaRows(1);
    }
  }, [prompt]);

  const handlePromptInputKeydown: KeyboardEventHandler = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (prompt.trim() !== "" && !isMessageStreamed) {
        handlePromptInputSubmit().then(() => {
          promptInputRef.current!.focus();
        });
      }
    }
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
      text: prompt,
      parameters: promptRequestParams,
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
                .replace(/<\/s>/, "")
                .trimEnd()
                .replace(/\\n/, "  \n");
              dispatch(
                updateMessage({ messageId: chatBotMessageId, chunk: newChunk }),
              );
            }
          }
        },
        onerror: (err) => {
          throw new Error(err);
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
    <div className="prompt-input-wrapper">
      <textarea
        ref={promptInputRef}
        id="prompt-input"
        className="w-full"
        value={prompt}
        onChange={handlePromptInputChange}
        onKeyDown={handlePromptInputKeydown}
        disabled={textFieldDisabled}
        rows={textAreaRows}
        placeholder="Enter your prompt..."
      />
      <button
        className={classNames({
          "icon-button": true,
          "animate-spin": isMessageStreamed,
        })}
        disabled={actionsDisabled}
        onClick={handlePromptInputSubmit}
      >
        {isMessageStreamed ? <BsHurricane /> : <BsSendFill />}
      </button>
    </div>
  );
};

export default PromptInput;
