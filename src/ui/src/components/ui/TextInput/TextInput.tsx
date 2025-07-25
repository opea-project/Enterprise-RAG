// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./TextInput.scss";

import classNames from "classnames";
import {
  forwardRef,
  HTMLAttributes,
  HTMLInputTypeAttribute,
  useId,
} from "react";
import { FieldError, Input, Label, TextField } from "react-aria-components";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

type TextInputSize = "sm";

interface TextInputProps extends HTMLAttributes<HTMLInputElement> {
  name: string;
  value: string | string[] | number | undefined;
  label?: string;
  type?: HTMLInputTypeAttribute;
  size?: TextInputSize;
  isCommaSeparated?: boolean;
  isDisabled?: boolean;
  isInvalid?: boolean;
  isReadOnly?: boolean;
  placeholder?: string;
  tooltipText?: string;
  errorMessage?: string;
}

const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  (
    {
      name,
      value,
      label,
      className,
      type = "text",
      size,
      isCommaSeparated,
      isDisabled,
      isInvalid,
      isReadOnly,
      placeholder,
      tooltipText,
      errorMessage,
      onChange,
      onKeyDown,
      ...rest
    },
    ref,
  ) => {
    const id = useId();
    const inputId = `${id}-text-input`;
    const errorId = `${id}-text-input-error`;

    return (
      <TextField
        isDisabled={isDisabled}
        isInvalid={isInvalid}
        isReadOnly={isReadOnly}
        aria-errormessage={isInvalid ? errorId : undefined}
        aria-invalid={isInvalid}
        aria-readonly={isReadOnly}
        aria-label={label ? label : name}
        className={classNames(
          "text-input",
          {
            "text-input--sm": size === "sm",
          },
          className,
        )}
      >
        {label && (
          <span className="text-input__label-wrapper">
            {tooltipText && (
              <Tooltip
                title={tooltipText}
                trigger={<InfoIcon aria-hidden="true" />}
                placement="left"
              />
            )}
            <Label htmlFor={inputId} className="text-input__label">
              {label}
            </Label>
          </span>
        )}
        <Input
          ref={ref}
          type={type}
          id={inputId}
          name={name}
          value={value}
          placeholder={placeholder}
          readOnly={isReadOnly}
          disabled={isDisabled}
          onChange={onChange}
          onKeyDown={onKeyDown}
          aria-description={
            isCommaSeparated ? "Enter values separated by commas" : undefined
          }
          aria-invalid={isInvalid}
          aria-label={name}
          aria-readonly={isReadOnly}
          className="text-input__input"
          {...rest}
        />
        {isInvalid && (
          <FieldError id={errorId} className="text-input__error">
            {errorMessage}
          </FieldError>
        )}
      </TextField>
    );
  },
);

export default TextInput;
