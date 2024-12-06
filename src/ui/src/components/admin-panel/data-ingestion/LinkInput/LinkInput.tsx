// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinkInput.scss";

import classNames from "classnames";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { BsPlus } from "react-icons/bs";
import { ValidationError } from "yup";

import { validateLinkInput } from "@/utils/data-ingestion/link-input";

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
    const checkValidity = async () => {
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
      checkValidity();
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
    addLinkToList(value);
    clearNewFileLinkInput();
    inputRef.current!.focus();
  };

  const addLinkBtnDisabled = !value || isInvalid || disabled;

  return (
    <div className="link-input-wrapper">
      <input
        ref={inputRef}
        value={value}
        className={classNames({ "input--invalid": isInvalid })}
        name="link-input"
        disabled={disabled}
        placeholder="Enter valid URL (starting with http:// or https://)"
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
