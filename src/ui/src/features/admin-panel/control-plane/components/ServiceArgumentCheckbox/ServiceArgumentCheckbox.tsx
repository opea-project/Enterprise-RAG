// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import CheckboxInput, {
  CheckboxInputChangeHandler,
} from "@/components/ui/CheckboxInput/CheckboxInput";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

export type ServiceArgumentCheckboxValue = boolean;

interface ServiceArgumentCheckboxProps {
  initialValue: ServiceArgumentCheckboxValue;
  name: string;
  tooltipText?: string;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentCheckbox = ({
  initialValue,
  name,
  tooltipText,
  onArgumentValueChange,
}: ServiceArgumentCheckboxProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
  const isDisabled = !isEditModeEnabled;

  const [isSelected, setIsSelected] =
    useState<ServiceArgumentCheckboxValue>(initialValue);

  useEffect(() => {
    if (isDisabled) {
      setIsSelected(initialValue);
    }
  }, [isDisabled, initialValue]);

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
      isDisabled={isDisabled}
      name={name}
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentCheckbox;
