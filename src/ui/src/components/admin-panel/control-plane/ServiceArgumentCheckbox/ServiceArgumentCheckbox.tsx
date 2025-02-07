// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentCheckbox.scss";

import classNames from "classnames";
import { ChangeEvent, useCallback, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";

interface ServiceArgumentCheckboxProps {
  initialValue: boolean;
  name: string;
  readOnly?: boolean;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: ServiceArgumentInputValue,
  ) => void;
}

const ServiceArgumentCheckbox = ({
  initialValue,
  name,
  readOnly,
  onArgumentValueChange,
}: ServiceArgumentCheckboxProps) => {
  const [checked, setChecked] = useState(initialValue);

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
    { "pointer-events-none": readOnly },
  ]);
  const inputClassNames = classNames([
    "service-argument-checkbox",
    { "pointer-events-none": readOnly },
  ]);

  return (
    <div className="service-argument-checkbox__wrapper">
      <label htmlFor={inputId} className={labelClassNames}>
        {name}
      </label>
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
