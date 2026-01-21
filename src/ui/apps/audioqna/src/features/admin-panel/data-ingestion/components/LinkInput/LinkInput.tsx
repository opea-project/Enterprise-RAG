// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  Button,
  IconButton,
  TextInput,
} from "@intel-enterprise-rag-ui/components";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ValidationError } from "yup";

import { validateLinkInput } from "@/features/admin-panel/data-ingestion/validators/linkInput";

interface LinkInputProps {
  addLinkToList: (value: string) => void;
}

const LinkInput = ({ addLinkToList }: LinkInputProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState("");
  const [isInvalid, setIsInvalid] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  useEffect(() => {
    const checkValidity = async (value: string) => {
      try {
        await validateLinkInput(value);
        setIsInvalid(false);
        setErrorMessage("");
      } catch (error) {
        setIsInvalid(true);
        setErrorMessage((error as ValidationError).message);
      }
    };

    if (value) {
      checkValidity(value);
    } else {
      setIsInvalid(false);
      setErrorMessage("");
    }
  }, [value]);

  const handleLinkInputKeyDown = (event: KeyboardEvent) => {
    if (!isInvalid && value.length > 0 && event.code === "Enter") {
      handleAddLinkBtnPress();
    }
  };

  const handleLinkInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
  };

  const clearNewFileLinkInput = () => {
    setValue("");
    inputRef.current!.focus();
  };

  const handleAddLinkBtnPress = () => {
    const sanitizedValue = sanitizeString(value);
    addLinkToList(sanitizedValue);
    clearNewFileLinkInput();
    inputRef.current!.focus();
  };

  const addLinkBtnDisabled = !value || isInvalid;

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const text = await file.text();

    const invalidLinks: string[] = [];

    const rawLinks = text
      .split(/[\n\r, ]+/)
      .map((link) => sanitizeString(link.trim()))
      .filter((link) => link.length > 0);

    if (rawLinks.length === 0 || !/^https?:\/\//.test(rawLinks[0])) {
      setUploadError("No valid links found in the uploaded file");
      return;
    }

    for (const link of rawLinks) {
      try {
        await validateLinkInput(link);
        addLinkToList(link);
      } catch {
        console.warn("Invalid link input skipped:", link);
        invalidLinks.push(link);
      }
    }

    if (invalidLinks.length > 0) {
      setUploadError(
        `The following link(s) were invalid and skipped: ${invalidLinks.join(", ")}`,
      );
    } else {
      setUploadError("");
    }
    event.target.value = "";
  };

  const handleBrowseFilesButtonPress = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-start gap-2">
        <TextInput
          ref={inputRef}
          type="url"
          value={value}
          name="link-input"
          isInvalid={isInvalid}
          errorMessage={errorMessage}
          placeholder="Enter valid URL (starting with http:// or https://)"
          className="w-full"
          onChange={handleLinkInputChange}
          onKeyDown={handleLinkInputKeyDown}
        />
        <IconButton
          icon="plus"
          variant="contained"
          aria-label="Add list to the list"
          isDisabled={addLinkBtnDisabled}
          onPress={handleAddLinkBtnPress}
        />
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-xs">
          You can also upload a <code>.txt</code> file with links separated by
          commas, spaces, or new lines. Each link must start with{" "}
          <code>http://</code> or <code>https://</code>
        </p>
        <Button size="sm" onPress={handleBrowseFilesButtonPress}>
          Browse Files
        </Button>
        {uploadError && (
          <div
            style={{
              color: "red",
              marginTop: "8px",
              fontSize: "0.875rem",
            }}
          >
            {uploadError}
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt"
          onChange={handleFileUpload}
          hidden
        />
      </div>
    </div>
  );
};

export default LinkInput;
