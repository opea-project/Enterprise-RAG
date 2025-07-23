// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ChangeEventHandler } from "react";

import TextAreaInput from "@/components/ui/TextAreaInput/TextAreaInput";
import { formatSnakeCaseToTitleCase } from "@/utils";

export type ServiceArgumentTextAreaValue = string;

interface ServiceArgumentTextAreaProps {
  value: string;
  placeholder: string;
  isInvalid: boolean;
  rows?: number;
  titleCaseLabel?: boolean;
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  inputConfig: {
    name: string;
    tooltipText?: string;
  };
}

const ServiceArgumentTextArea = ({
  value,
  placeholder,
  isInvalid,
  rows = 3,
  titleCaseLabel = true,
  onChange,
  inputConfig: { name, tooltipText },
}: ServiceArgumentTextAreaProps) => {
  const label = titleCaseLabel ? formatSnakeCaseToTitleCase(name) : name;

  return (
    <TextAreaInput
      name={name}
      value={value}
      label={label}
      size="sm"
      placeholder={placeholder}
      rows={rows}
      isInvalid={isInvalid}
      tooltipText={tooltipText}
      onChange={onChange}
    />
  );
};

export default ServiceArgumentTextArea;
