// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  PlaySpeechButtonState,
  selectChatById,
} from "@intel-enterprise-rag-ui/chat";
import { addNotification } from "@intel-enterprise-rag-ui/components";
import { useCallback, useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";
import { useParams } from "react-router-dom";

import { useTextToSpeechMutation } from "@/features/chat/api/tts.api";
import { isAbortError } from "@/features/chat/utils/api";
import { useAppSelector } from "@/store/hooks";

interface UseTextToSpeechResult {
  playingTurnId: string | null;
  playingState: PlaySpeechButtonState;
  onPlayMessage: (turnId: string) => Promise<void>;
}

export const useTextToSpeech = (): UseTextToSpeechResult => {
  const [textToSpeech] = useTextToSpeechMutation();

  const [playingTurnId, setCurrentTurnId] = useState<string | null>(null);
  const [playingState, setPlayingState] =
    useState<PlaySpeechButtonState>("idle");

  const { chatId } = useParams<{ chatId?: string }>();
  const chat = useAppSelector((state) => selectChatById(state, chatId));
  const dispatch = useDispatch();

  const currentAbortControllerRef = useRef<AbortController | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);

  const cleanup = useCallback(() => {
    if (currentAbortControllerRef.current) {
      currentAbortControllerRef.current.abort();
      currentAbortControllerRef.current = null;
    }

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    if (currentAudioUrlRef.current) {
      URL.revokeObjectURL(currentAudioUrlRef.current);
      currentAudioUrlRef.current = null;
    }

    setCurrentTurnId(null);
    setPlayingState("idle");
  }, []);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const handleAudioErrorWithAbort = useCallback(
    (abortController: AbortController, error: unknown) => {
      // Only show notification if this is still the current request
      if (currentAbortControllerRef.current !== abortController) {
        return;
      }

      // Do not show error notification for aborted requests (user clicks button for another message)
      if (isAbortError(error)) {
        cleanup();
        return;
      }

      let errorMessage = "Failed to generate audio";
      if (error instanceof Error || error instanceof MediaError) {
        errorMessage = error.message;
      }

      cleanup();
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    },
    [cleanup, dispatch],
  );

  const onPlayMessage = useCallback(
    async (turnId: string) => {
      const turn = chat?.turns.find((turn) => turn.id === turnId);

      if (!turn || !turn.answer || !turn.answer.trim()) {
        return;
      }

      const abortController = new AbortController();
      cleanup();
      currentAbortControllerRef.current = abortController;
      setCurrentTurnId(turnId);
      setPlayingState("waiting");

      try {
        const { audioUrl } = await textToSpeech({
          input: turn.answer,
          signal: abortController.signal,
        }).unwrap();

        currentAudioUrlRef.current = audioUrl;

        const audio = new Audio(audioUrl);
        currentAudioRef.current = audio;

        audio.oncanplay = () => {
          setPlayingState("playing");
          audio.play().catch((err) => {
            handleAudioErrorWithAbort(abortController, err);
          });
        };
        audio.onended = () => {
          cleanup();
        };
        audio.onerror = () => {
          handleAudioErrorWithAbort(abortController, audio.error);
        };
      } catch (err) {
        handleAudioErrorWithAbort(abortController, err);
      }
    },
    [chat?.turns, cleanup, textToSpeech, handleAudioErrorWithAbort],
  );

  return {
    playingTurnId,
    playingState,
    onPlayMessage,
  };
};
