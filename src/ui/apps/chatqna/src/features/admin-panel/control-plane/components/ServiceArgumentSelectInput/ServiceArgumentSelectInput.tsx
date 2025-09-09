// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  SelectInput,
  SelectInputChangeHandler,
} from "@intel-enterprise-rag-ui/components";
import { useEffect, useState } from "react";

import { OnArgumentValueChangeHandler } from "@/features/admin-panel/control-plane/types";

export type ServiceArgumentSelectInputValue = string;

interface ServiceArgumentSelectInputProps {
  name: string;
  value: ServiceArgumentSelectInputValue;
  options: string[];
  tooltipText?: string;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

const ServiceArgumentSelectInput = ({
  name,
  value,
  options,
  tooltipText,
  onArgumentValueChange,
}: ServiceArgumentSelectInputProps) => {
  const [selected, setSelected] =
    useState<ServiceArgumentSelectInputValue>(value);

  useEffect(() => {
    setSelected(value);
  }, [value]);

  const handleChange: SelectInputChangeHandler<
    ServiceArgumentSelectInputValue
  > = (item) => {
    setSelected(item);
    onArgumentValueChange(name, item);
  };

  return (
    <SelectInput
      value={selected}
      items={options}
      label={name}
      name={name}
      size="sm"
      tooltipText={tooltipText}
      fullWidth
      onChange={handleChange}
    />
  );
};

export default ServiceArgumentSelectInput;
