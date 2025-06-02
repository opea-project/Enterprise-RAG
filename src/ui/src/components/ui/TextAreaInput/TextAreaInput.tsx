// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./TextAreaInput.scss";

import classNames from "classnames";
import { HTMLAttributes, useId } from "react";
import { Label, TextArea, TextField } from "react-aria-components";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

type TextAreaInputSize = "sm";

interface TextAreaInputProps extends HTMLAttributes<HTMLTextAreaElement> {
  name: string;
  value: string;
  label?: string;
  size?: TextAreaInputSize;
  isInvalid?: boolean;
  placeholder?: string;
  tooltipText?: string;
}

const TextAreaInput = ({
  name,
  value,
  label,
  size,
  isInvalid,
  placeholder,
  tooltipText,
  ...restProps
}: TextAreaInputProps) => {
  const id = useId();
  const inputId = `${id}-textarea-input`;

  return (
    <TextField
      isInvalid={isInvalid}
      aria-invalid={isInvalid}
      className={classNames("textarea-input", {
        "textarea-input--sm": size === "sm",
      })}
    >
      {label && (
        <span className="textarea-input__label-wrapper">
          {tooltipText && (
            <Tooltip
              title={tooltipText}
              trigger={<InfoIcon aria-hidden="true" />}
              placement="left"
            />
          )}
          <Label htmlFor={inputId} className="textarea-input__label">
            {label}
          </Label>
        </span>
      )}
      <TextArea
        value={value}
        id={inputId}
        name={name}
        placeholder={placeholder}
        className="textarea-input__input"
        aria-invalid={isInvalid}
        {...restProps}
      />
    </TextField>
  );
};

export default TextAreaInput;
