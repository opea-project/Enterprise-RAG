// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./TextInput.scss";

import { InfoIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import {
  forwardRef,
  HTMLAttributes,
  HTMLInputTypeAttribute,
  useId,
} from "react";
import {
  FieldError as AriaFieldError,
  Input as AriaInput,
  TextField as AriaTextField,
} from "react-aria-components";

import { Label } from "@/Label/Label";
import { Tooltip } from "@/Tooltip/Tooltip";

type TextInputSize = "sm";

interface TextInputProps extends HTMLAttributes<HTMLInputElement> {
  /** Name of the text input */
  name: string;
  /** Value of the text input */
  value: string | string[] | number | undefined;
  /** Label for the text input */
  label?: string;
  /** Input type (e.g., text, password) */
  type?: HTMLInputTypeAttribute;
  /** Size of the text input */
  size?: TextInputSize;
  /** If true, allows comma separated values */
  isCommaSeparated?: boolean;
  /** If true, disables the input */
  isDisabled?: boolean;
  /** If true, marks the input as invalid */
  isInvalid?: boolean;
  /** If true, makes the input read-only */
  isReadOnly?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Tooltip text for additional info */
  tooltipText?: string;
  /** Error message to display */
  errorMessage?: string;
}

/**
 * Text input component with label, validation, tooltip, and error support.
 */
export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
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
      <AriaTextField
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
            <Label htmlFor={inputId} size={size}>
              {label}
            </Label>
          </span>
        )}
        <AriaInput
          ref={ref}
          type={type}
          id={inputId}
          name={name}
          value={value}
          placeholder={placeholder}
          readOnly={isReadOnly}
          disabled={isDisabled}
          aria-description={
            isCommaSeparated ? "Enter values separated by commas" : undefined
          }
          aria-invalid={isInvalid}
          aria-label={name}
          aria-readonly={isReadOnly}
          className="text-input__input"
          onChange={onChange}
          onKeyDown={onKeyDown}
          {...rest}
        />
        {isInvalid && (
          <AriaFieldError id={errorId} className="text-input__error">
            {errorMessage}
          </AriaFieldError>
        )}
      </AriaTextField>
    );
  },
);

TextInput.displayName = "TextInput";
