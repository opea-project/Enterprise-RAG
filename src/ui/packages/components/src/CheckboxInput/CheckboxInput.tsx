// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./CheckboxInput.scss";

import { CheckboxCheckIcon, InfoIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useId } from "react";
import {
  Checkbox as AriaCheckbox,
  CheckboxProps as AriaCheckboxProps,
  Label as AriaLabel,
} from "react-aria-components";

import { Tooltip } from "@/Tooltip/Tooltip";

type CheckboxInputSize = "sm";
export type CheckboxInputChangeHandler = (isSelected: boolean) => void;

interface CheckboxInputProps extends AriaCheckboxProps {
  /** Label for the checkbox input (optional for standalone checkboxes) */
  label?: string;
  /** Size of the checkbox input */
  size?: CheckboxInputSize;
  /** Tooltip text for additional info */
  tooltipText?: string;
  /** If true, renders checkbox in dense mode */
  dense?: boolean;
  /** Callback for value change */
  onChange: CheckboxInputChangeHandler;
}

/**
 * Checkbox input component for boolean selection, with label, tooltip, and dense mode support.
 */
export const CheckboxInput = ({
  label,
  size,
  tooltipText,
  dense,
  onChange,
  isRequired,
  ...rest
}: CheckboxInputProps) => {
  const inputId = useId();

  return (
    <div
      className={classNames("checkbox-input", {
        "checkbox-input--sm": size === "sm",
        "checkbox-input--dense": dense,
        "checkbox-input--standalone": !label,
      })}
    >
      <AriaCheckbox
        id={inputId}
        className="checkbox-input__input"
        aria-required={isRequired}
        onChange={onChange}
        {...rest}
      >
        {({ isSelected }) =>
          isSelected ? <CheckboxCheckIcon aria-hidden="true" /> : null
        }
      </AriaCheckbox>
      {label && (
        <span>
          <AriaLabel htmlFor={inputId} className="checkbox-input__label">
            {label}
          </AriaLabel>
          {tooltipText && (
            <Tooltip
              title={tooltipText}
              trigger={<InfoIcon />}
              placement="left"
            />
          )}
        </span>
      )}
    </div>
  );
};
