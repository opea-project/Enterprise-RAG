// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentNumberInput.scss";

import classNames from "classnames";
import { ChangeEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { ValidationError } from "yup";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { validateServiceArgumentNumberInput } from "@/features/admin-panel/control-plane/validators/service-arguments/numberInput";
import { useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";
import { NumberInputRange } from "@/utils/validators/types";

export type ServiceArgumentNumberInputValue =
  | string
  | number
  | undefined
  | null;

interface ServiceArgumentNumberInputProps {
  name: string;
  initialValue: ServiceArgumentNumberInputValue;
  range: NumberInputRange;
  tooltipText?: string;
  nullable?: boolean;
  readOnlyDisabled?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentNumberInput = ({
  name,
  initialValue,
  range,
  tooltipText,
  nullable = false,
  readOnlyDisabled = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  const isGraphEditModeEnabled = useAppSelector(
    chatQnAGraphEditModeEnabledSelector,
  );
  const isEditModeEnabled = readOnlyDisabled
    ? readOnlyDisabled
    : isGraphEditModeEnabled;
  const readOnly = !isEditModeEnabled;

  const [value, setValue] = useState(initialValue || "");
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (readOnly) {
      setValue(initialValue ?? "");
      setIsInvalid(false);
    }
  }, [readOnly, initialValue]);

  const validateInput = async (value: string) => {
    try {
      await validateServiceArgumentNumberInput(value, range, nullable);
      setIsInvalid(false);
      setError("");
      return true;
    } catch (validationError) {
      setIsInvalid(true);
      setError((validationError as ValidationError).message);
      return false;
    }
  };

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setValue(newValue);
    const sanitizedValue = sanitizeString(newValue);
    const isValid = await validateInput(sanitizedValue);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const argumentValue = parseFloat(sanitizedValue) || null;
      onArgumentValueChange(name, argumentValue);
    }
  };

  const inputClassNames = classNames({
    "service-argument-number-input": true,
    "input--invalid": isInvalid,
  });

  const inputId = `${name}-number-input-${uuidv4()}`;
  const placeholder = `Enter number between ${range.min} and ${range.max}`;

  return (
    <div className="service-argument-number-input__wrapper">
      <label htmlFor={inputId} className="service-argument-number-input__label">
        {tooltipText && (
          <Tooltip
            title={tooltipText}
            trigger={<InfoIcon />}
            placement="right"
          />
        )}
        <span>{name}</span>
      </label>
      <input
        className={inputClassNames}
        value={value}
        id={inputId}
        name={inputId}
        type="text"
        placeholder={placeholder}
        readOnly={readOnly}
        onChange={handleChange}
      />
      {isInvalid && <p className="error mt-1 pl-2 text-xs italic">{error}</p>}
    </div>
  );
};

export default ServiceArgumentNumberInput;
