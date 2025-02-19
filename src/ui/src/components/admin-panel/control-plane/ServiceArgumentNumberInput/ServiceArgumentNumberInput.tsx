// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentNumberInput.scss";

import classNames from "classnames";
import { ChangeEvent, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { object, string, ValidationError } from "yup";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/shared/Tooltip/Tooltip";
import { chatQnAGraphEditModeEnabledSelector } from "@/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/admin-panel/control-plane";
import { sanitizeString } from "@/utils";
import { isInRange, isValidNumber } from "@/utils/validators/textInput";

export type ServiceArgumentNumberInputValue =
  | string
  | number
  | undefined
  | null;

interface ServiceArgumentNumberInputProps {
  name: string;
  initialValue: ServiceArgumentNumberInputValue;
  range: { min: number; max: number };
  tooltipText?: string;
  nullable?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentNumberInput = ({
  name,
  initialValue,
  range,
  tooltipText,
  nullable = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentNumberInputProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
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

  const validationSchema = object().shape({
    numberInput: string()
      .test("is-valid-number", "Enter a valid number value", isValidNumber)
      .test(
        "is-in-range",
        `Enter number between ${range.min} and ${range.max}`,
        isInRange(nullable, range),
      ),
  });

  const validateInput = async (value: string) => {
    try {
      await validationSchema.validate({ numberInput: value });
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
          <Tooltip text={tooltipText} position="right">
            <InfoIcon />
          </Tooltip>
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
