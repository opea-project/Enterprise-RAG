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
import TextInput from "@/components/ui/TextInput/TextInput";
import { PostToExtractTextQueryParams } from "@/features/admin-panel/data-ingestion/types/api";
import useDebug from "@/hooks/useDebug";

interface TextExtractionFormProps {
  isLoadingExtractedText: boolean;
  onFormSubmit: (
    queryParams: PostToExtractTextQueryParams,
    isFormEnabled: boolean,
  ) => void;
}

export const TextExtractionForm = ({
  isLoadingExtractedText,
  onFormSubmit,
}: TextExtractionFormProps) => {
  const [formData, setFormData] = useState<PostToExtractTextQueryParams>({
    chunk_size: 0,
    chunk_overlap: 0,
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

  const handleEnableFormCheckboxChange = (isSelected: boolean) => {
    setIsFormEnabled(isSelected);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onFormSubmit(formData, isFormEnabled);
  };

  const isFormDisabled = isLoadingExtractedText || !isFormEnabled;

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
        <TextInput
          label="Chunk Size (0-9999)"
          type="number"
          name="chunk_size"
          value={formData.chunk_size}
          isDisabled={isFormDisabled}
          onChange={handleRangeInputChange}
        />
        <TextInput
          label="Chunk Overlap (0-9999)"
          type="number"
          name="chunk_overlap"
          value={formData.chunk_overlap}
          isDisabled={isFormDisabled}
          onChange={handleRangeInputChange}
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
    queryParams: PostToExtractTextQueryParams,
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
