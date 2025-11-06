// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UploadFileTab.scss";

import {
  addNotification,
  FileInput,
  FileInputHandle,
} from "@intel-enterprise-rag-ui/components";
import { sanitizeFile } from "@intel-enterprise-rag-ui/utils";
import { ChangeEvent, DragEvent, useCallback, useRef } from "react";

import { useSummarizeFileMutation } from "@/features/docsum/api";
import GeneratedSummary from "@/features/docsum/components/shared/GeneratedSummary/GeneratedSummary";
import GenerateSummaryButton from "@/features/docsum/components/shared/GenerateSummaryButton/GenerateSummaryButton";
import FileSelectedToSummarize from "@/features/docsum/components/tabs/upload-file/FileSelectedToSummarize/FileSelectedToSummarize";
import { addHistoryItem } from "@/features/docsum/store/history.slice";
import {
  clearUploadFileTab,
  selectUploadFileTabState,
  setErrorMessage,
  setFileData,
  setIsLoading,
  setStreamingText,
  setSummary,
} from "@/features/docsum/store/uploadFileTab.slice";
import {
  convertToApiFileData,
  documentToBase64,
} from "@/features/docsum/utils/api";
import { validateFileInput } from "@/features/docsum/validators/fileInput";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const SUPPORTED_FILE_EXTENSIONS = ["pdf", "doc", "docx", "md"];

const CLIENT_MAX_BODY_SIZE = 64; // in MB, should be in sync with server configuration

const UploadFileTab = () => {
  const [summarizeFile, { data }] = useSummarizeFileMutation();

  const dispatch = useAppDispatch();
  const { fileData, summary, streamingText, isLoading, errorMessage } =
    useAppSelector(selectUploadFileTabState);

  const fileInputRef = useRef<FileInputHandle>(null);
  const summaryRef = useRef("");

  const processFile = useCallback(
    async (file: File) => {
      const sanitizedFile = sanitizeFile(file);
      const validationMessage = await validateFileInput(sanitizedFile);
      dispatch(setErrorMessage(validationMessage));
      if (validationMessage === "") {
        // Convert file to base64 and store in Redux
        const base64 = await documentToBase64(sanitizedFile);
        dispatch(
          setFileData({
            name: sanitizedFile.name,
            size: sanitizedFile.size,
            type: sanitizedFile.type,
            base64,
          }),
        );
      }

      fileInputRef.current?.clear();
    },
    [dispatch],
  );

  const handleFileInputDrop = useCallback(
    async (event: DragEvent) => {
      event.preventDefault();

      const file = event.dataTransfer?.files[0] ?? null;
      if (file !== null) {
        await processFile(file);
      }
    },
    [processFile],
  );

  const handleFileInputChange = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files![0] ?? null;
      if (file !== null && file instanceof File) {
        await processFile(file);
      }

      summaryRef.current = "";
      dispatch(setStreamingText(""));
    },
    [processFile, dispatch],
  );

  const isGeneratingSummary = !fileData || isLoading;

  const handleGenerateSummaryButtonPress = useCallback(async () => {
    if (fileData !== null) {
      summaryRef.current = "";
      dispatch(setStreamingText(""));
      dispatch(setIsLoading(true));

      const handleUpdate = (chunk: string) => {
        summaryRef.current += chunk;
        dispatch(setStreamingText(summaryRef.current));
      };

      // Convert Redux FileData to API FileData format
      const apiFileData = convertToApiFileData(fileData);

      const { data, error } = await summarizeFile({
        fileData: apiFileData,
        onSummaryUpdate: handleUpdate,
      });

      dispatch(setIsLoading(false));

      if (error) {
        console.error("File summary error:", error);
        dispatch(
          addNotification({
            severity: "error",
            text: `An error occurred while summarizing the file: ${JSON.stringify(error)}`,
          }),
        );
      } else {
        const summaryToSave = summaryRef.current || data?.text || "";
        if (summaryToSave) {
          summaryRef.current = summaryToSave;
          dispatch(setSummary(summaryToSave));
          dispatch(
            addHistoryItem({
              title: fileData.name,
              sourceType: "file",
              summary: summaryToSave,
              source: fileData.name,
            }),
          );
          dispatch(
            addNotification({
              severity: "success",
              text: `The summary for ${fileData.name} has been saved successfully.`,
            }),
          );
        }
      }
      dispatch(setStreamingText(""));
    }
  }, [fileData, summarizeFile, dispatch]);

  const handleChangeFileButtonPress = () => {
    fileInputRef.current!.click();
  };

  const handleDeleteFileButtonPress = () => {
    fileInputRef.current!.clear();
    dispatch(clearUploadFileTab());
    summaryRef.current = "";
  };

  return (
    <div className="upload-file-tab">
      <div className="upload-file-tab__upload-col">
        <p>File to Summarize</p>
        {fileData && (
          <FileSelectedToSummarize
            fileName={fileData.name}
            isGeneratingSummary={isGeneratingSummary}
            onChangeFile={handleChangeFileButtonPress}
            onDeleteFile={handleDeleteFileButtonPress}
          />
        )}
        <FileInput
          ref={fileInputRef}
          errorMessage={errorMessage}
          totalSizeLimit={CLIENT_MAX_BODY_SIZE}
          className={`${fileData ? "hidden" : "visible"}`}
          supportedFileExtensions={SUPPORTED_FILE_EXTENSIONS}
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
          summary={summary}
          isLoading={isLoading}
          fileName={fileData?.name}
          data={data}
          streamingText={streamingText}
        />
      </div>
    </div>
  );
};

export default UploadFileTab;
