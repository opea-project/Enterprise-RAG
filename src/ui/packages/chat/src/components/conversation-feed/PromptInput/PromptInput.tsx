// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInput.scss";

import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import {
  ChangeEvent,
  ChangeEventHandler,
  FormEventHandler,
  KeyboardEventHandler,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  TextArea as AriaTextArea,
  TextField as AriaTextField,
} from "react-aria-components";

import { PromptInputButton } from "@/components/conversation-feed/PromptInputButton/PromptInputButton";

const MAX_REQUEST_BODY_SIZE = 1 * 1024 * 1024; // 1MB in bytes - restriction from nginx config
const REQUEST_BODY_FORMAT_OVERHEAD = '{ "text": "" }'.length;
const PROMPT_MAX_LENGTH = MAX_REQUEST_BODY_SIZE - REQUEST_BODY_FORMAT_OVERHEAD;
const PROMPT_MAX_HEIGHT = 15 * 16; // must be the same as max-height set for prompt-input css class

interface PromptInputProps {
  prompt: string;
  isChatResponsePending?: boolean;
  enableMicrophone?: boolean;
  onRequestAbort?: () => void;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  onSubmit: (prompt: string) => void;
  onSpeechToText?: (audioBlob: Blob) => Promise<string>;
  onSpeechToTextError?: (error: Error) => void;
}

export const PromptInput = ({
  prompt,
  isChatResponsePending = false,
  enableMicrophone = false,
  onRequestAbort,
  onChange,
  onSubmit,
  onSpeechToText,
  onSpeechToTextError,
}: PromptInputProps) => {
  const promptInputRef = useRef<HTMLTextAreaElement | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  const isMediaRecorderSupported =
    typeof MediaRecorder !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function";

  useEffect(() => {
    focusPromptInput();
  }, []);

  useEffect(() => {
    recalcuatePromptInputHeight();
  }, [prompt]);

  useEffect(() => {
    return () => {
      stopMediaStream();
    };
  }, []);

  const stopMediaStream = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  };

  const focusPromptInput = () => {
    promptInputRef.current!.focus();
  };

  const recalcuatePromptInputHeight = () => {
    const promptInput = promptInputRef.current;
    if (promptInput !== null) {
      const currentHeight = promptInput.style.height;
      promptInput.style.height = "auto";
      const targetHeight = `${promptInput.scrollHeight}px`;
      promptInput.style.height = currentHeight;

      const maxHeight = PROMPT_MAX_HEIGHT;
      const targetHeightNumber = parseInt(targetHeight, 10);
      promptInput.style.overflowY =
        targetHeightNumber > maxHeight ? "scroll" : "hidden";

      requestAnimationFrame(() => {
        promptInput.style.height = targetHeight;
      });
    }
  };

  const isSubmitDisabled = useCallback(() => {
    const sanitizedPrompt = sanitizeString(prompt).trim();
    const isPromptEmpty = sanitizedPrompt.length === 0;
    const isPromptMaxLengthExceeded =
      sanitizedPrompt.length > PROMPT_MAX_LENGTH;

    return isPromptEmpty || isPromptMaxLengthExceeded;
  }, [prompt]);

  const submitPrompt = () => {
    const sanitizedPrompt = sanitizeString(prompt).trim();
    onSubmit(sanitizedPrompt);

    focusPromptInput();
  };

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    submitPrompt();
  };

  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isSubmitDisabled() && !isChatResponsePending) {
        submitPrompt();
      }
    }
  };

  const handleStopBtnPress = () => {
    onRequestAbort?.();
    focusPromptInput();
  };

  const handleStopBtnKeyDown: KeyboardEventHandler = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onRequestAbort?.();
      focusPromptInput();
    }
  };

  const appendTranscriptToInput = (transcript: string) => {
    if (transcript && transcript !== "[BLANK_AUDIO]") {
      const separator = prompt.length > 0 ? " " : "";
      const syntheticEvent = {
        target: {
          value: `${prompt}${separator}${transcript}`,
        },
      } as ChangeEvent<HTMLTextAreaElement>;
      onChange(syntheticEvent);
    }
  };

  const startRecording = async () => {
    if (!onSpeechToText) {
      console.error(
        "onSpeechToText callback is required for microphone functionality",
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType,
        });
        stopMediaStream();

        if (audioBlob.size > 0 && onSpeechToText) {
          try {
            const transcript = await onSpeechToText(audioBlob);
            appendTranscriptToInput(transcript.trim());
          } catch (error) {
            console.error("Speech-to-text transcription failed:", error);
            onSpeechToTextError?.(
              error instanceof Error
                ? error
                : new Error("Transcription failed"),
            );
          } finally {
            setIsTranscribing(false);
            focusPromptInput();
          }
        } else {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.onerror = () => {
        setIsRecording(false);
        stopMediaStream();
        onSpeechToTextError?.(new Error("Recording failed"));
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Failed to start recording:", error);
      onSpeechToTextError?.(
        error instanceof Error
          ? error
          : new Error("Failed to access microphone"),
      );
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      setIsTranscribing(true);
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleMicrophoneBtnPress = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const showStopButton = onRequestAbort && isChatResponsePending;
  const showSendButton = !showStopButton;
  const showMicrophoneButton =
    enableMicrophone && isMediaRecorderSupported && onSpeechToText;

  const isMicrophoneButtonDisabled =
    (isChatResponsePending && !isRecording) || isTranscribing;

  const formClassName = useMemo(
    () =>
      showMicrophoneButton
        ? "prompt-input__form prompt-input__form--with-microphone"
        : "prompt-input__form",
    [showMicrophoneButton],
  );

  const microphoneButtonIcon = useMemo(
    () => (isRecording ? "microphone-recording" : "microphone"),
    [isRecording],
  );

  const microphoneButtonAriaLabel = useMemo(
    () => (isRecording ? "Stop recording" : "Start recording"),
    [isRecording],
  );

  const microphoneButtonClassName = useMemo(
    () =>
      classNames({
        "prompt-input__button--recording": isRecording,
      }),
    [isRecording],
  );

  return (
    <form
      className={formClassName}
      onSubmit={handleSubmit}
      data-testid="prompt-input-form"
    >
      <AriaTextField
        className="prompt-input__text-field"
        aria-label="Your message"
      >
        <AriaTextArea
          ref={promptInputRef}
          value={prompt}
          name="prompt-input"
          placeholder="Enter your prompt..."
          maxLength={PROMPT_MAX_LENGTH}
          rows={1}
          className="prompt-input"
          data-testid="prompt-input-textarea"
          onChange={onChange}
          onKeyDown={handleKeyDown}
        />
      </AriaTextField>
      {showStopButton && (
        <PromptInputButton
          data-testid="prompt-stop-button"
          icon="prompt-stop"
          type="button"
          aria-label="Stop response"
          onPress={handleStopBtnPress}
          onKeyDown={handleStopBtnKeyDown}
        />
      )}
      {showMicrophoneButton && (
        <PromptInputButton
          data-testid="prompt-microphone-button"
          icon={microphoneButtonIcon}
          type="button"
          aria-label={microphoneButtonAriaLabel}
          className={microphoneButtonClassName}
          isDisabled={isMicrophoneButtonDisabled}
          onPress={handleMicrophoneBtnPress}
        />
      )}
      {showSendButton && (
        <PromptInputButton
          data-testid="prompt-send-button"
          icon="prompt-send"
          type="submit"
          aria-label="Send prompt"
          isDisabled={isSubmitDisabled()}
        />
      )}
    </form>
  );
};
