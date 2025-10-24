// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadFileTab.scss";

import {
  addNotification,
  FileInput,
  FileInputHandle,
} from "@intel-enterprise-rag-ui/components";
import {
  ChangeEvent,
  DragEvent,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";

import { useSummarizeFileMutation } from "@/api";
import GeneratedSummary from "@/components/GeneratedSummary/GeneratedSummary";
import GenerateSummaryButton from "@/components/GenerateSummaryButton/GenerateSummaryButton";
import { addHistoryItem } from "@/features/tabs/history/store/history.slice";
import FileSelectedToSummarize from "@/features/tabs/upload-file/FileSelectedToSummarize/FileSelectedToSummarize";
import { useAppDispatch } from "@/store/hooks";

const SUPPORTED_FILE_EXTENSIONS = ["pdf", "doc", "docx", "md"];

const CLIENT_MAX_BODY_SIZE = 64; // in MB, should be in sync with server configuration

const UploadFileTab = () => {
  const [summarizeFile, { isLoading, data }] = useSummarizeFileMutation();

  const fileInputRef = useRef<FileInputHandle>(null);
  const [errorMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const dispatch = useAppDispatch();

  const handleFileInputDrop = useCallback(async (event: DragEvent) => {
    event.preventDefault();
    setFile(event.dataTransfer.files![0] || null);
  }, []);

  const handleFileInputChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      setFile((prevFile) => event.target.files![0] || prevFile || null);
    },
    [],
  );

  const isGeneratingSummary = useMemo(
    () => !file || isLoading,
    [file, isLoading],
  );

  const handleGenerateSummaryButtonPress = useCallback(async () => {
    if (file !== null) {
      const { data, error } = await summarizeFile({ file });
      if (data) {
        dispatch(
          addHistoryItem({
            title: file.name,
            sourceType: "file",
            summary: data.summary,
            source: file.name,
          }),
        );
        dispatch(
          addNotification({
            severity: "success",
            text: `The summary for ${file.name} has been saved successfully.`,
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
  }, [file, summarizeFile, dispatch]);

  const handleChangeFileButtonPress = useCallback(() => {
    fileInputRef.current!.click();
  }, []);

  const handleDeleteFileButtonPress = useCallback(() => {
    fileInputRef.current!.clear();
    setFile(null);
  }, []);

  return (
    <div className="upload-file-tab">
      <div className="upload-file-tab__upload-col">
        <p>File to Summarize</p>
        {file && (
          <FileSelectedToSummarize
            fileName={file.name}
            isGeneratingSummary={isGeneratingSummary}
            onChangeFile={handleChangeFileButtonPress}
            onDeleteFile={handleDeleteFileButtonPress}
          />
        )}
        <FileInput
          ref={fileInputRef}
          errorMessage={errorMessage}
          totalSizeLimit={CLIENT_MAX_BODY_SIZE}
          className={`${file ? "hidden" : "visible"}`}
          supportedFileExtensions={[...SUPPORTED_FILE_EXTENSIONS]}
          onDrop={handleFileInputDrop}
          onChange={handleFileInputChange}
        />
        <GenerateSummaryButton
          isDisabled={isGeneratingSummary}
          onPress={handleGenerateSummaryButtonPress}
        />
      </div>
      <div className="upload-file-tab__summary-col">
        <GeneratedSummary
          summary={data?.summary}
          isLoading={isLoading}
          fileName={file?.name}
        />
      </div>
    </div>
  );
};

export default UploadFileTab;
