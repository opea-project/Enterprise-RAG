// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PasteTextTab.scss";

import {
  addNotification,
  Button,
  Label,
  TextAreaInput,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEventHandler, useCallback, useEffect, useRef } from "react";
import { ValidationError } from "yup";

import { useSummarizePlainTextMutation } from "@/features/docsum/api";
import GeneratedSummary from "@/features/docsum/components/shared/GeneratedSummary/GeneratedSummary";
import GenerateSummaryButton from "@/features/docsum/components/shared/GenerateSummaryButton/GenerateSummaryButton";
import { addHistoryItem } from "@/features/docsum/store/history.slice";
import {
  clearPasteTextTab,
  selectPasteTextTabState,
  setErrorMessage,
  setIsInvalid,
  setIsLoading,
  setStreamingText,
  setSummary,
  setText,
} from "@/features/docsum/store/pasteTextTab.slice";
import { validateTextAreaInput } from "@/features/docsum/validators/textAreaInput";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { shortenText } from "@/utils/text";

const PasteTextTab = () => {
  const [summarizePlainText, { data }] = useSummarizePlainTextMutation();

  const dispatch = useAppDispatch();
  const { text, summary, streamingText, isLoading, errorMessage, isInvalid } =
    useAppSelector(selectPasteTextTabState);

  const summaryRef = useRef("");

  useEffect(() => {
    const checkValidity = async (text: string) => {
      try {
        await validateTextAreaInput(text);
        dispatch(setIsInvalid(false));
        dispatch(setErrorMessage(""));
      } catch (error) {
        dispatch(setIsInvalid(true));
        dispatch(setErrorMessage((error as ValidationError).message));
      }
    };

    if (text) {
      checkValidity(text);
    } else {
      dispatch(setIsInvalid(false));
      dispatch(setErrorMessage(""));
    }
  }, [text, dispatch]);

  const focusTextArea = () => {
    const textArea = document.querySelector("textarea[name='paste-text']");
    if (textArea instanceof HTMLTextAreaElement) {
      textArea.focus();
    }
  };

  const clearText = () => {
    dispatch(clearPasteTextTab());
    summaryRef.current = "";
    focusTextArea();
  };

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    dispatch(setText(event.target.value));
  };

  const handleGenerateSummaryButtonPress = useCallback(async () => {
    if (text.trim()) {
      summaryRef.current = "";
      dispatch(setSummary(""));
      dispatch(setStreamingText(""));
      dispatch(setIsLoading(true));

      const handleUpdate = (chunk: string) => {
        summaryRef.current += chunk;
        dispatch(setStreamingText(summaryRef.current));
      };

      const { data, error } = await summarizePlainText({
        text,
        onSummaryUpdate: handleUpdate,
      });

      dispatch(setIsLoading(false));

      if (error) {
        console.error("Text summary error:", error);
        dispatch(
          addNotification({
            severity: "error",
            text: `An error occurred while summarizing the text: ${JSON.stringify(error)}`,
          }),
        );
      } else {
        const summaryToSave = summaryRef.current ?? data?.text ?? "";
        if (summaryToSave) {
          summaryRef.current = summaryToSave;
          dispatch(setSummary(summaryToSave));
          dispatch(
            addHistoryItem({
              title: shortenText(text),
              sourceType: "plainText",
              summary: summaryToSave,
              source: text,
            }),
          );
          dispatch(
            addNotification({
              severity: "success",
              text: "The summary for the pasted text has been saved successfully.",
            }),
          );
        }
      }
      dispatch(setStreamingText(""));
    }
  }, [text, summarizePlainText, dispatch]);

  const isGeneratingSummaryDisabled = !text.trim() || isLoading;
  const isClearBtnDisabled =
    text.trim().length === 0 || isGeneratingSummaryDisabled;

  return (
    <div className="paste-text-tab">
      <div className="paste-text-tab__text-area-col">
        <div className="paste-text-tab__text-area-col__header">
          <Label htmlFor="paste-text">Text to Summarize</Label>
          <Button
            size="sm"
            variant="outlined"
            isDisabled={isClearBtnDisabled}
            onPress={clearText}
          >
            Clear
          </Button>
        </div>
        <TextAreaInput
          id="paste-text"
          name="paste-text"
          value={text}
          placeholder="Paste your text here..."
          className="paste-text-tab__text-area"
          aria-label="Paste your text here"
          disabled={isLoading}
          onChange={handleChange}
          isInvalid={isInvalid}
        />
        <p className="paste-text-tab__error-message">{errorMessage}</p>
        <GenerateSummaryButton
          isDisabled={isGeneratingSummaryDisabled}
          onPress={handleGenerateSummaryButtonPress}
        />
      </div>
      <div className="paste-text-tab__summary-col">
        <GeneratedSummary
          summary={summary}
          isLoading={isLoading}
          fileName={shortenText(text)}
          data={data}
          streamingText={streamingText}
        />
      </div>
    </div>
  );
};

export default PasteTextTab;
