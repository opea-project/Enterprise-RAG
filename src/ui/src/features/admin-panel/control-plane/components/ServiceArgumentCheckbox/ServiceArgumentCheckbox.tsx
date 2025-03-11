// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentCheckbox.scss";

import classNames from "classnames";
import { ChangeEvent, useCallback, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

export type ServiceArgumentCheckboxValue = boolean;

interface ServiceArgumentCheckboxProps {
  initialValue: ServiceArgumentCheckboxValue;
  name: string;
  tooltipText?: string;
  hideLabel?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentCheckbox = ({
  initialValue,
  name,
  tooltipText,
  hideLabel,
  onArgumentValueChange,
}: ServiceArgumentCheckboxProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
  const readOnly = !isEditModeEnabled;

  const [checked, setChecked] =
    useState<ServiceArgumentCheckboxValue>(initialValue);

  useEffect(() => {
    if (readOnly) {
      setChecked(initialValue);
    }
  }, [readOnly, initialValue]);

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setChecked(event.target.checked);
      onArgumentValueChange(name, event.target.checked);
    },
    [name, onArgumentValueChange],
  );

  const inputId = `${name}-checkbox-${uuidv4()}`;

  const labelClassNames = classNames([
    "service-argument-checkbox__label",
    { "pointer-events-none": readOnly, "m-0": hideLabel },
  ]);
  const inputClassNames = classNames([
    "service-argument-checkbox",
    { "pointer-events-none": readOnly, "m-0": hideLabel },
  ]);

  return (
    <div className="service-argument-checkbox__wrapper">
      {!hideLabel && (
        <label htmlFor={inputId} className={labelClassNames}>
          {tooltipText && (
            <Tooltip text={tooltipText} position="right">
              <InfoIcon />
            </Tooltip>
          )}
          <span>{name}</span>
        </label>
      )}
      <input
        className={inputClassNames}
        type="checkbox"
        id={inputId}
        name={inputId}
        checked={checked}
        onChange={handleChange}
      />
    </div>
  );
};

export default ServiceArgumentCheckbox;
