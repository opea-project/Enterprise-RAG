// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./TextAreaInput.scss";

import { InfoIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useId } from "react";
import {
  TextArea as AriaTextArea,
  TextAreaProps as AriaTextAreaProps,
  TextField as AriaTextField,
} from "react-aria-components";

import { Label } from "@/Label/Label";
import { Tooltip } from "@/Tooltip/Tooltip";

type TextAreaInputSize = "sm";

interface TextAreaInputProps extends AriaTextAreaProps {
  /** Name of the textarea input */
  name: string;
  /** Value of the textarea input */
  value: string;
  /** Label for the textarea input */
  label?: string;
  /** Size of the textarea input */
  size?: TextAreaInputSize;
  /** Marks the input as invalid */
  isInvalid?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Tooltip text for additional info */
  tooltipText?: string;
}

/**
 * Textarea input component with label, validation, and tooltip support.
 */
export const TextAreaInput = ({
  name,
  value,
  label,
  size,
  isInvalid,
  placeholder,
  tooltipText,
  className,
  ...rest
}: TextAreaInputProps) => {
  const id = useId();
  const inputId = `${id}-textarea-input`;

  return (
    <AriaTextField
      isInvalid={isInvalid}
      aria-invalid={isInvalid}
      className={classNames(
        "textarea-input",
        {
          "textarea-input--sm": size === "sm",
          "textarea-input--with-label": label,
        },
        className,
      )}
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
          <Label htmlFor={inputId} size={size}>
            {label}
          </Label>
        </span>
      )}
      <AriaTextArea
        value={value}
        id={inputId}
        name={name}
        placeholder={placeholder}
        className="textarea-input__input"
        aria-invalid={isInvalid}
        {...rest}
      />
    </AriaTextField>
  );
};
