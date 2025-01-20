// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinkInput.scss";

import classNames from "classnames";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { BsPlus } from "react-icons/bs";
import { ValidationError } from "yup";

import { sanitizeString } from "@/utils";
import {
  urlErrorMessage,
  validateLinkInput,
} from "@/utils/data-ingestion/link-input";

interface LinkInputProps {
  addLinkToList: (value: string) => void;
  disabled: boolean;
}

const LinkInput = ({ addLinkToList, disabled }: LinkInputProps) => {
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

  const addLinkBtnDisabled = !value || isInvalid || disabled;

  return (
    <div className="link-input-wrapper">
      <input
        ref={inputRef}
        value={value}
        name="link-input"
        type="url"
        placeholder="Enter valid URL (starting with http:// or https://)"
        className={classNames({ "input--invalid": isInvalid })}
        disabled={disabled}
        onChange={handleLinkInputChange}
        onKeyDown={handleLinkInputKeyDown}
      />
      <button
        className="icon-button-outlined--primary"
        disabled={addLinkBtnDisabled}
        onClick={handleAddNewLinkItem}
      >
        <BsPlus />
      </button>
      {isInvalid && <p className="link-input-error-message">{errorMessage}</p>}
    </div>
  );
};

export default LinkInput;
