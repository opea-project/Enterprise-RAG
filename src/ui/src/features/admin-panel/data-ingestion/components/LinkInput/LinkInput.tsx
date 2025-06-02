// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ValidationError } from "yup";

import IconButton from "@/components/ui/IconButton/IconButton";
import TextInput from "@/components/ui/TextInput/TextInput";
import { linkErrorMessage } from "@/features/admin-panel/data-ingestion/utils/constants";
import { validateLinkInput } from "@/features/admin-panel/data-ingestion/validators/linkInput";
import { sanitizeString } from "@/utils";

interface LinkInputProps {
  addLinkToList: (value: string) => void;
}

const LinkInput = ({ addLinkToList }: LinkInputProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState("");
  const [isInvalid, setIsInvalid] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const checkValidity = async (value: string) => {
      try {
        const sanitizedValue = sanitizeString(value);
        if (value !== sanitizedValue) {
          throw new Error(linkErrorMessage);
        }

        await validateLinkInput(sanitizedValue);
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

  return (
    <div className="flex items-start gap-2">
      <TextInput
        ref={inputRef}
        type="url"
        value={value}
        name="link-input"
        isInvalid={isInvalid}
        errorMessage={errorMessage}
        placeholder="Enter valid URL (starting with http:// or https://)"
        onChange={handleLinkInputChange}
        onKeyDown={handleLinkInputKeyDown}
        className="w-full"
      />
      <IconButton
        icon="plus"
        variant="contained"
        aria-label="Add list to the list"
        isDisabled={addLinkBtnDisabled}
        onPress={handleAddLinkBtnPress}
      />
    </div>
  );
};

export default LinkInput;
