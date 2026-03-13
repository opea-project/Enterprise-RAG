// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  SelectInput,
  SelectInputChangeHandler,
} from "@intel-enterprise-rag-ui/components";
import { useEffect, useState } from "react";

import {
  OnArgumentValueChangeHandler,
  ServiceArgumentSelectInputValue,
} from "@/types/index";

interface ServiceArgumentSelectInputProps {
  name: string;
  value: ServiceArgumentSelectInputValue;
  options: string[];
  tooltipText?: string;
  onArgumentValueChange: OnArgumentValueChangeHandler;
}

export const ServiceArgumentSelectInput = ({
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
      data-testid={`service-argument-select-input-${name}`}
      value={selected}
      items={options}
      label={name}
      name={name}
      size="sm"
      tooltipText={tooltipText}
      onChange={handleChange}
      fullWidth
    />
  );
};
