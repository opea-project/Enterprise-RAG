// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import CheckboxInput, {
  CheckboxInputChangeHandler,
} from "@/components/ui/CheckboxInput/CheckboxInput";
import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";

export type ServiceArgumentCheckboxValue = boolean;

interface ServiceArgumentCheckboxProps {
  value: ServiceArgumentCheckboxValue;
  name: string;
  tooltipText?: string;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentCheckbox = ({
  value,
  name,
  tooltipText,
  onArgumentValueChange,
}: ServiceArgumentCheckboxProps) => {
  const [isSelected, setIsSelected] =
    useState<ServiceArgumentCheckboxValue>(value);

  useEffect(() => {
    setIsSelected(value);
  }, [value]);

  const handleChange: CheckboxInputChangeHandler = useCallback(
    (isSelected) => {
      setIsSelected(isSelected);
      onArgumentValueChange(name, isSelected);
    },
    [name, onArgumentValueChange],
  );

  return (
    <CheckboxInput
      label={name}
      size="sm"
      tooltipText={tooltipText}
      isSelected={isSelected}
      name={name}
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentCheckbox;
