// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentCheckbox.scss";

import { ChangeEvent, useCallback, useState } from "react";

import { chatQnAGraphEditModeEnabledSelector } from "@/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

interface ServiceArgumentCheckboxProps {
  initialValue: boolean;
  name: string;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: string | number | boolean | null,
  ) => void;
}

const ServiceArgumentCheckbox = ({
  initialValue,
  name,
  onArgumentValueChange,
}: ServiceArgumentCheckboxProps) => {
  const [checked, setChecked] = useState(initialValue);

  const editModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  const disabled = !editModeEnabled;

  const handleChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      setChecked(event.target.checked);
      onArgumentValueChange(name, event.target.checked);
    },
    [name, onArgumentValueChange],
  );

  return (
    <input
      className="service-argument-checkbox"
      type="checkbox"
      name={name}
      disabled={disabled}
      checked={checked}
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentCheckbox;
