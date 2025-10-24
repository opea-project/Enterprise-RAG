// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PasteTextTab.scss";

import {
  addNotification,
  Button,
  TextAreaInput,
} from "@intel-enterprise-rag-ui/components";
import { ChangeEventHandler, useCallback, useMemo, useState } from "react";

import { useSummarizePlainTextMutation } from "@/api";
import GeneratedSummary from "@/components/GeneratedSummary/GeneratedSummary";
import GenerateSummaryButton from "@/components/GenerateSummaryButton/GenerateSummaryButton";
import { addHistoryItem } from "@/features/tabs/history/store/history.slice";
import { useAppDispatch } from "@/store/hooks";
import { shortenText } from "@/utils/text";

const CHARACTER_LIMIT = 1000;

const PasteTextTab = () => {
  const [summarizePlainText, { isLoading, data }] =
    useSummarizePlainTextMutation();
  const [text, setText] = useState("");

  const dispatch = useAppDispatch();

  const focusTextArea = () => {
    const textArea = document.querySelector("textarea[name='paste-text']");
    if (textArea instanceof HTMLTextAreaElement) {
      textArea.focus();
    }
  };

  const clearText = () => {
    setText("");
    focusTextArea();
  };

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = useCallback(
    (event) => {
      if (event.target.value.length > CHARACTER_LIMIT) {
        setText(event.target.value.slice(0, CHARACTER_LIMIT));
      } else {
        setText(event.target.value);
      }
    },
    [],
  );

  const handleGenerateSummaryButtonPress = useCallback(async () => {
    if (text) {
      const { data, error } = await summarizePlainText({ text });

      if (data) {
        dispatch(
          addHistoryItem({
            title: shortenText(text),
            sourceType: "plainText",
            summary: data.summary,
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
      if (error) {
        dispatch(
          addNotification({
            severity: "error",
            text: "An error occurred while summarizing the file. Please try again.",
          }),
        );
      }
    }
  }, [text, summarizePlainText, dispatch]);

  const isGeneratingSummaryDisabled = useMemo(
    () => !text || isLoading,
    [text, isLoading],
  );

  const isClearBtnDisabled = useMemo(
    () => text.length === 0 || isGeneratingSummaryDisabled,
    [isGeneratingSummaryDisabled, text.length],
  );

  return (
    <div className="paste-text-tab">
      <div className="paste-text-tab__text-area-col">
        <div className="paste-text-tab__text-area-col__header">
          <p>Text to Summarize</p>
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
          name="paste-text"
          value={text}
          placeholder="Paste your text here..."
          className="paste-text-tab__text-area"
          aria-label="Paste your text here"
          disabled={isLoading}
          onChange={handleChange}
        />
        <p className="paste-text-tab__char-limit">
          Character Limit: {text.length} / {CHARACTER_LIMIT}
        </p>
        <GenerateSummaryButton
          isDisabled={isGeneratingSummaryDisabled}
          onPress={handleGenerateSummaryButtonPress}
        />
      </div>
      <div className="paste-text-tab__summary-col">
        <GeneratedSummary
          summary={data?.summary}
          isLoading={isLoading}
          fileName={shortenText(text)}
        />
      </div>
    </div>
  );
};

export default PasteTextTab;
