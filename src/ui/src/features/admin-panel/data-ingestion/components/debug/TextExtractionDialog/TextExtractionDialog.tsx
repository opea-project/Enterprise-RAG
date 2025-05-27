// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./TextExtractionDialog.scss";

import {
  ChangeEventHandler,
  FormEvent,
  useMemo,
  useRef,
  useState,
} from "react";

import Button from "@/components/ui/Button/Button";
import CheckboxInput from "@/components/ui/CheckboxInput/CheckboxInput";
import Dialog from "@/components/ui/Dialog/Dialog";
import LoadingFallback from "@/components/ui/LoadingFallback/LoadingFallback";
import { ExtractTextQueryParamsFormData } from "@/features/admin-panel/data-ingestion/types";
import useDebug from "@/hooks/useDebug";

interface TextExtractionFormProps {
  isLoadingExtractedText: boolean;
  onFormSubmit: (
    queryParams: ExtractTextQueryParamsFormData,
    isFormEnabled: boolean,
  ) => void;
}

export const TextExtractionForm = ({
  isLoadingExtractedText,
  onFormSubmit,
}: TextExtractionFormProps) => {
  const [formData, setFormData] = useState<ExtractTextQueryParamsFormData>({
    chunk_size: 0,
    chunk_overlap: 0,
    process_table: false,
    table_strategy: false,
  });
  const [isFormEnabled, setIsFormEnabled] = useState<boolean>(false);

  const handleRangeInputChange: ChangeEventHandler<HTMLInputElement> = (
    event,
  ) => {
    const { name, value } = event.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: Math.max(0, Math.min(Number(value), 9999)),
    }));
  };

  const handleCheckboxInputChange = (name: string, isSelected: boolean) => {
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: isSelected,
    }));
  };

  const handleEnableFormCheckboxChange = (isSelected: boolean) => {
    setIsFormEnabled(isSelected);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onFormSubmit(formData, isFormEnabled);
  };

  const formDisabled = isLoadingExtractedText || !isFormEnabled;

  return (
    <div className="text-extraction-dialog__content-form-column">
      <CheckboxInput
        label="Use Parameters"
        name="use-parameters"
        isSelected={isFormEnabled}
        isDisabled={isLoadingExtractedText}
        onChange={handleEnableFormCheckboxChange}
      />
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
        <CheckboxInput
          label="Process Table"
          name="process_table"
          isSelected={formData.process_table}
          isDisabled={formDisabled}
          onChange={(isSelected) =>
            handleCheckboxInputChange("process_table", isSelected)
          }
        />
        <CheckboxInput
          label="Table Strategy: Fast"
          name="table_strategy"
          isSelected={formData.table_strategy}
          isDisabled={formDisabled}
          onChange={(isSelected) =>
            handleCheckboxInputChange("table_strategy", isSelected)
          }
        />
        <Button type="submit" isDisabled={isLoadingExtractedText}>
          Extract Text
        </Button>
      </form>
    </div>
  );
};

interface ExtractedTextProps {
  extractedText: string;
}

const ExtractedText = ({ extractedText }: ExtractedTextProps) => {
  const linesPerPage = 40;
  const [visibleTextOffset, setVisibleTextOffset] = useState(linesPerPage);

  const formattedExtractedText = useMemo(
    () => JSON.stringify(extractedText ?? "", null, 2),
    [extractedText],
  );
  const maxVisibleTextOffset = formattedExtractedText.split("\n").length;

  const visibleFormattedExtractedText = useMemo(
    () =>
      formattedExtractedText.split("\n").slice(0, visibleTextOffset).join("\n"),
    [formattedExtractedText, visibleTextOffset],
  );

  const isLoadMoreButtonVisible =
    visibleTextOffset < maxVisibleTextOffset &&
    formattedExtractedText.length > 0;

  const handleLoadMoreTextButtonPress = () => {
    setVisibleTextOffset((prevOffset) => prevOffset + linesPerPage);
  };

  return (
    <div className="extracted-text">
      <pre>{visibleFormattedExtractedText}</pre>
      {isLoadMoreButtonVisible && (
        <Button
          size="sm"
          variant="outlined"
          fullWidth
          onPress={handleLoadMoreTextButtonPress}
        >
          Load more text...
        </Button>
      )}
    </div>
  );
};

interface TextExtractionDialogProps {
  objectName: string;
  extractedText?: string;
  isLoading: boolean;
  errorMessage?: string;
  onTriggerPress: () => void;
  onFormSubmit: (
    queryParams: ExtractTextQueryParamsFormData,
    isFormEnabled: boolean,
  ) => void;
}

const TextExtractionDialog = ({
  objectName,
  extractedText,
  isLoading,
  errorMessage,
  onTriggerPress,
  onFormSubmit,
}: TextExtractionDialogProps) => {
  const ref = useRef<HTMLDialogElement>(null);
  const handleClose = () => ref.current?.close();
  const showDialog = () => ref.current?.showModal();

  const { isDebugEnabled } = useDebug();

  if (!isDebugEnabled) {
    return null;
  }

  const handlePress = async () => {
    showDialog();
    onTriggerPress();
  };

  const trigger = (
    <Button size="sm" variant="outlined" onPress={handlePress}>
      Extract Text
    </Button>
  );

  const dialogTitle = `${objectName} - Extracted Text`;

  const getContent = () => {
    if (isLoading) {
      return (
        <LoadingFallback loadingMessage="Extracting text... Be patient, it may take a while." />
      );
    }

    if (extractedText === undefined) {
      if (errorMessage) {
        return <p className="error">{errorMessage}</p>;
      }
      return <p>No text extracted from the file</p>;
    }

    return <ExtractedText extractedText={extractedText} />;
  };

  return (
    <Dialog
      ref={ref}
      trigger={trigger}
      title={dialogTitle}
      onClose={handleClose}
    >
      <div className="text-extraction-dialog__content">
        <TextExtractionForm
          isLoadingExtractedText={isLoading}
          onFormSubmit={onFormSubmit}
        />

        {getContent()}
      </div>
    </Dialog>
  );
};

export default TextExtractionDialog;
