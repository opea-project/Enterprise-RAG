// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { addNotification } from "@intel-enterprise-rag-ui/components";
import { useCallback } from "react";

import { useSpeechToTextMutation } from "@/features/chat/api/asr.api";
import { useAppDispatch } from "@/store/hooks";
import { convertToWav } from "@/utils/audioConverter";

export const useSpeechToTextHandlers = () => {
  const dispatch = useAppDispatch();
  const [speechToText] = useSpeechToTextMutation();

  const handleSpeechToText = useCallback(
    async (audioBlob: Blob) => {
      const wavBlob = await convertToWav(audioBlob);
      const result = await speechToText({ audio: wavBlob }).unwrap();
      return result.text;
    },
    [speechToText],
  );

  const handleSpeechToTextError = useCallback(
    (error: Error) => {
      dispatch(
        addNotification({
          severity: "error",
          text: `Speech-to-text failed: ${error.message}`,
        }),
      );
    },
    [dispatch],
  );

  return {
    handleSpeechToText,
    handleSpeechToTextError,
  };
};
