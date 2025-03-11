// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentTextInput.scss";

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
import { validateServiceArgumentTextInput } from "@/features/admin-panel/control-plane/validators/service-arguments/textInput";
import { useAppSelector } from "@/store/hooks";
import { sanitizeString } from "@/utils";

export type ServiceArgumentTextInputValue = string | string[] | null;

interface ServiceArgumentTextInputProps {
  name: string;
  initialValue: ServiceArgumentTextInputValue;
  tooltipText?: string;
  nullable?: boolean;
  commaSeparated?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
  onArgumentValidityChange: OnArgumentValidityChangeHandler;
}

const ServiceArgumentTextInput = ({
  name,
  initialValue,
  tooltipText,
  nullable = false,
  commaSeparated = false,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentTextInputProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
  const readOnly = !isEditModeEnabled;

  const [value, setValue] = useState(initialValue ?? "");
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
      await validateServiceArgumentTextInput(value, nullable);
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
    setIsInvalid(!isValid);
    onArgumentValidityChange(name, !isValid);
    if (isValid) {
      const isValueEmpty = newValue.trim() === "";
      const argumentValue = isValueEmpty && nullable ? null : sanitizedValue;
      onArgumentValueChange(name, argumentValue);
    }
  };

  const inputClassNames = classNames({
    "service-argument-text-input": true,
    "input--invalid": isInvalid,
  });

  const inputId = `${name}-text-input-${uuidv4()}`;
  const placeholder = commaSeparated ? "Enter values separated by comma" : "";

  return (
    <div className="service-argument-text-input__wrapper">
      <label htmlFor={inputId} className="service-argument-text-input__label">
        {tooltipText && (
          <Tooltip text={tooltipText} position="right">
            <InfoIcon />
          </Tooltip>
        )}
        <span>{name}</span>
      </label>
      <input
        className={inputClassNames}
        type="text"
        id={inputId}
        name={inputId}
        value={value}
        placeholder={placeholder}
        readOnly={readOnly}
        onChange={handleChange}
      />
      {isInvalid && <p className="error mt-1 pl-2 text-xs italic">{error}</p>}
    </div>
  );
};

export default ServiceArgumentTextInput;
