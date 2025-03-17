// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./FileTextExtractionDialog.scss";

import { ChangeEventHandler, FormEvent, useRef, useState } from "react";

import Button from "@/components/ui/Button/Button";
import Dialog from "@/components/ui/Dialog/Dialog";
import LoadingFallback from "@/components/ui/LoadingFallback/LoadingFallback";
import { postFileToExtractText } from "@/features/admin-panel/data-ingestion/api/postFileToExtractText";
import { ExtractTextQueryParamsFormData } from "@/features/admin-panel/data-ingestion/types";
import useDebug from "@/hooks/useDebug";

interface FileTextExtractionFormProps {
  isLoadingExtractedText: boolean;
  onFormSubmit: (queryParams: ExtractTextQueryParamsFormData) => void;
}

export const FileTextExtractionForm = ({
  isLoadingExtractedText,
  onFormSubmit,
}: FileTextExtractionFormProps) => {
  const [formData, setFormData] = useState<ExtractTextQueryParamsFormData>({
    chunk_size: 0,
    chunk_overlap: 0,
    process_table: false,
    table_strategy: false,
  });
  const [formEnabled, setFormEnabled] = useState<boolean>(false);

  const handleRangeInputChange: ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    const { name, value } = event.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: Math.max(0, Math.min(Number(value), 9999)),
    }));
  };

  const handleCheckboxInputChange: ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    const { name, checked } = event.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: checked,
    }));
  };

  const handleEnableFormCheckboxChange: ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    setFormEnabled(event.target.checked);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    onFormSubmit(formData);
  };

  const formDisabled = isLoadingExtractedText || !formEnabled;

  return (
    <div className="file-text-extraction-dialog__content-form-column">
      <div>
        <input
          type="checkbox"
          id="use-parameters"
          name="use-parameters"
          checked={formEnabled}
          disabled={isLoadingExtractedText}
          onChange={handleEnableFormCheckboxChange}
        />
        <label htmlFor="use-parameters">Use Parameters</label>
      </div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="chunk_size">Chunk Size (0-9999)</label>
          <input
            type="number"
            id="chunk_size"
            name="chunk_size"
            min={0}
            max={9999}
            value={formData.chunk_size}
            readOnly={formDisabled}
            onChange={handleRangeInputChange}
          />
        </div>
        <div>
          <label htmlFor="chunk_overlap">Chunk Overlap (0-9999)</label>
          <input
            type="number"
            id="chunk_overlap"
            name="chunk_overlap"
            min={0}
            max={9999}
            value={formData.chunk_overlap}
            readOnly={formDisabled}
            onChange={handleRangeInputChange}
          />
        </div>
        <div>
          <label htmlFor="process_table">Process Table</label>
          <input
            type="checkbox"
            id="process_table"
            name="process_table"
            checked={formData.process_table}
            disabled={formDisabled}
            onChange={handleCheckboxInputChange}
          />
        </div>
        <div>
          <label htmlFor="table_strategy">Table Strategy: Fast</label>
          <input
            type="checkbox"
            id="table_strategy"
            name="table_strategy"
            checked={formData.table_strategy}
            disabled={formDisabled}
            onChange={handleCheckboxInputChange}
          />
        </div>
        <Button type="submit" disabled={isLoadingExtractedText}>
          Extract Text
        </Button>
      </form>
    </div>
  );
};

interface FileTextExtractionDialogProps {
  fileUuid: string;
  fileName: string;
}

const FileTextExtractionDialog = ({
  fileUuid,
  fileName,
}: FileTextExtractionDialogProps) => {
  const [extractedText, setExtractedText] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const ref = useRef<HTMLDialogElement>(null);
  const handleClose = () => ref.current?.close();
  const showDialog = () => ref.current?.showModal();

  const { isDebugEnabled } = useDebug();

  if (!isDebugEnabled) {
    return null;
  }

  const extractText = async (
    uuid: string,
    queryParams?: ExtractTextQueryParamsFormData,
  ) => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      setExtractedText(null);
      const text = await postFileToExtractText(uuid, queryParams);
      setExtractedText(text);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to extract text from the file";
      setErrorMessage(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClick = async () => {
    showDialog();
    extractText(fileUuid);
  };

  const onFormSubmit = (queryParams: ExtractTextQueryParamsFormData) => {
    extractText(fileUuid, queryParams);
  };

  const trigger = (
    <Button size="sm" variant="outlined" onClick={handleClick}>
      Extract Text
    </Button>
  );

  const dialogTitle = `${fileName} - Extracted Text`;

  const getContent = () => {
    if (isLoading) {
      return (
        <LoadingFallback loadingMessage="Extracting text... Be patient, it may take a while." />
      );
    }

    if (extractedText === null) {
      if (errorMessage) {
        return <p className="error">{errorMessage}</p>;
      }
      return <p>No text extracted from the file</p>;
    }

    const formattedExtractedText = JSON.stringify(extractedText, null, 2);

    return <pre>{formattedExtractedText}</pre>;
  };

  return (
    <Dialog
      ref={ref}
      trigger={trigger}
      title={dialogTitle}
      onClose={handleClose}
    >
      <div className="file-text-extraction-dialog__content">
        <FileTextExtractionForm
          isLoadingExtractedText={isLoading}
          onFormSubmit={onFormSubmit}
        />
        {getContent()}
      </div>
    </Dialog>
  );
};

export default FileTextExtractionDialog;
