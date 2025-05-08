// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentSelectInput.scss";

import classNames from "classnames";
import { ChangeEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

export type ServiceArgumentSelectInputValue = string;

interface ServiceArgumentSelectInputProps {
  name: string;
  initialValue: ServiceArgumentSelectInputValue;
  options: string[];
  tooltipText?: string;
  readOnlyDisabled?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentSelectInput = ({
  name,
  initialValue,
  options,
  tooltipText,
  readOnlyDisabled = false,
  onArgumentValueChange,
}: ServiceArgumentSelectInputProps) => {
  const isGraphEditModeEnabled = useAppSelector(
    chatQnAGraphEditModeEnabledSelector,
  );
  const isEditModeEnabled = readOnlyDisabled
    ? readOnlyDisabled
    : isGraphEditModeEnabled;
  const readOnly = !isEditModeEnabled;

  const [value, setValue] =
    useState<ServiceArgumentSelectInputValue>(initialValue);

  useEffect(() => {
    if (readOnly) {
      setValue(initialValue);
    }
  }, [readOnly, initialValue]);

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setValue(event.target.value);
    onArgumentValueChange(name, event.target.value);
  };

  const inputId = `${name}-select-input-${uuidv4()}`;
  const inputClassNames = classNames([
    "service-argument-select-input",
    { "pointer-events-none": readOnly, "input--read-only": readOnly },
  ]);

  return (
    <>
      <label htmlFor={inputId} className="service-argument-select-input__label">
        {tooltipText && (
          <Tooltip
            title={tooltipText}
            trigger={<InfoIcon />}
            placement="left"
          />
        )}
        <span>{name}</span>
      </label>
      <select
        id={inputId}
        name={name}
        className={inputClassNames}
        value={value}
        onChange={handleChange}
      >
        {options.map((option, index) => (
          <option key={inputId + index} value={option}>
            {option}
          </option>
        ))}
      </select>
    </>
  );
};

export default ServiceArgumentSelectInput;
