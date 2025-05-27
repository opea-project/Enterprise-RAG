// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./CheckboxInput.scss";

import classNames from "classnames";
import { useId } from "react";
import { Checkbox, CheckboxProps, Label } from "react-aria-components";
import { BsCheck } from "react-icons/bs";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

type CheckboxInputSize = "sm";
export type CheckboxInputChangeHandler = (isSelected: boolean) => void;

interface CheckboxInputProps extends CheckboxProps {
  label: string;
  size?: CheckboxInputSize;
  tooltipText?: string;
  onChange: CheckboxInputChangeHandler;
}

const CheckboxInput = ({
  label,
  size,
  tooltipText,
  onChange,
  isRequired,
  ...restProps
}: CheckboxInputProps) => {
  const inputId = useId();

  const wrapperClassNames = classNames("checkbox-input__wrapper", {
    "checkbox-input__wrapper--sm": size === "sm",
  });

  const checkboxClassNames = classNames("checkbox-input", {
    "checkbox-input--sm": size === "sm",
  });

  const labelClassNames = classNames("checkbox-input__label", {
    "checkbox-input__label--sm": size === "sm",
  });

  return (
    <div className={wrapperClassNames}>
      <Checkbox
        id={inputId}
        className={checkboxClassNames}
        onChange={onChange}
        aria-required={isRequired}
        {...restProps}
      >
        {({ isSelected }) =>
          isSelected ? <BsCheck aria-hidden="true" /> : null
        }
      </Checkbox>
      <span>
        <Label htmlFor={inputId} className={labelClassNames}>
          {label}
        </Label>
        {tooltipText && (
          <Tooltip
            title={tooltipText}
            trigger={<InfoIcon />}
            placement="left"
          />
        )}
      </span>
    </div>
  );
};

export default CheckboxInput;
