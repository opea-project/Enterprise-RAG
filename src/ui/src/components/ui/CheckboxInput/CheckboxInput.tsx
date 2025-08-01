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
  dense?: boolean;
  onChange: CheckboxInputChangeHandler;
}

const CheckboxInput = ({
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
      })}
    >
      <Checkbox
        id={inputId}
        className="checkbox-input__input"
        onChange={onChange}
        aria-required={isRequired}
        {...rest}
      >
        {({ isSelected }) =>
          isSelected ? <BsCheck aria-hidden="true" /> : null
        }
      </Checkbox>
      <span>
        <Label htmlFor={inputId} className="checkbox-input__label">
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
