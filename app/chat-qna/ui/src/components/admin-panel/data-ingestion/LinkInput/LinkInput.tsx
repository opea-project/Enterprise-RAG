// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LinkInput.scss";

import AddIcon from "@mui/icons-material/Add";
import { TextField, Typography } from "@mui/material";
import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import ClearInputIconButton from "@/components/shared/ClearInputIconButton/ClearInputIconButton";
import SquareIconButton from "@/components/shared/SquareIconButton/SquareIconButton";

const isLinkInvalid = (value: string) => {
  try {
    const newLink = new URL(value);
    const hostnameItems = newLink.hostname.split(".");
    return (
      !["http:", "https:"].includes(newLink.protocol) ||
      hostnameItems.length < 2 ||
      !hostnameItems.every((item) => item.length > 1)
    );
  } catch (e) {
    console.error(e);
    return true;
  }
};

interface LinkInputProps {
  addLinkToList: (value: string) => void;
  disabled: boolean;
}

const LinkInput = ({ addLinkToList, disabled }: LinkInputProps) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [value, setValue] = useState("");
  const [isInvalid, setIsInvalid] = useState(false);

  useEffect(() => {
    setIsInvalid(value.length > 0 && isLinkInvalid(value));
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

  const clearInputBtnDisabled = !value || disabled;
  const addLinkBtnDisabled = !value || isInvalid || disabled;

  return (
    <div className="link-input-wrapper">
      <div className="link-input">
        <TextField
          inputRef={inputRef}
          value={value}
          error={isInvalid}
          disabled={disabled}
          placeholder="Enter valid URL (starting with http or https)"
          onChange={handleLinkInputChange}
          onKeyDown={handleLinkInputKeyDown}
          InputProps={{
            endAdornment: (
              <ClearInputIconButton
                disabled={clearInputBtnDisabled}
                onClick={clearNewFileLinkInput}
              />
            ),
          }}
        />
        {isInvalid && (
          <Typography variant="caption" color="error" className="error-message">
            Please enter valid URL that starts with protocol (http or https)
          </Typography>
        )}
      </div>
      <SquareIconButton
        disabled={addLinkBtnDisabled}
        onClick={handleAddNewLinkItem}
      >
        <AddIcon fontSize="small" />
      </SquareIconButton>
    </div>
  );
};

export default LinkInput;
