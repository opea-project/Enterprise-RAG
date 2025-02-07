// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinkInput.scss";

import classNames from "classnames";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ValidationError } from "yup";

import IconButton from "@/components/shared/IconButton/IconButton";
import { sanitizeString } from "@/utils";
import {
  urlErrorMessage,
  validateLinkInput,
} from "@/utils/data-ingestion/link-input";

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
          throw new Error(urlErrorMessage);
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
      handleAddNewLinkItem();
    }
  };

  const handleLinkInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setValue(event.target.value);
  };

  const clearNewFileLinkInput = () => {
    setValue("");
    inputRef.current!.focus();
  };

  const handleAddNewLinkItem = () => {
    const sanitizedValue = sanitizeString(value);
    addLinkToList(sanitizedValue);
    clearNewFileLinkInput();
    inputRef.current!.focus();
  };

  const addLinkBtnDisabled = !value || isInvalid;

  return (
    <div className="link-input-wrapper">
      <input
        ref={inputRef}
        value={value}
        name="link-input"
        type="url"
        placeholder="Enter valid URL (starting with http:// or https://)"
        className={classNames({ "input--invalid": isInvalid })}
        onChange={handleLinkInputChange}
        onKeyDown={handleLinkInputKeyDown}
      />
      <IconButton
        icon="plus"
        variant="contained"
        disabled={addLinkBtnDisabled}
        onClick={handleAddNewLinkItem}
      />
      {isInvalid && <p className="link-input-error-message">{errorMessage}</p>}
    </div>
  );
};

export default LinkInput;
