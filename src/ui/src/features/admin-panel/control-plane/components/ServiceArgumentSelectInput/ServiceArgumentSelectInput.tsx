// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

import SelectInput, {
  SelectInputChangeHandler,
} from "@/components/ui/SelectInput/SelectInput";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

export type ServiceArgumentSelectInputValue = string;

interface ServiceArgumentSelectInputProps {
  name: string;
  initialValue: ServiceArgumentSelectInputValue;
  options: string[];
  tooltipText?: string;
  isReadOnlyDisabled?: boolean;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentSelectInput = ({
  name,
  initialValue,
  options,
  tooltipText,
  isReadOnlyDisabled = false,
  onArgumentValueChange,
}: ServiceArgumentSelectInputProps) => {
  const isGraphEditModeEnabled = useAppSelector(
    chatQnAGraphEditModeEnabledSelector,
  );
  const isEditModeEnabled = isReadOnlyDisabled
    ? isReadOnlyDisabled
    : isGraphEditModeEnabled;
  const isReadOnly = !isEditModeEnabled;

  const [value, setValue] =
    useState<ServiceArgumentSelectInputValue>(initialValue);

  useEffect(() => {
    if (isReadOnly) {
      setValue(initialValue);
    }
  }, [isReadOnly, initialValue]);

  const handleChange: SelectInputChangeHandler<
    ServiceArgumentSelectInputValue
  > = (item) => {
    setValue(item);
    onArgumentValueChange(name, item);
  };

  return (
    <SelectInput
      value={value}
      items={options}
      label={name}
      name={name}
      size="sm"
      isDisabled={isReadOnly}
      tooltipText={tooltipText}
      fullWidth
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentSelectInput;
