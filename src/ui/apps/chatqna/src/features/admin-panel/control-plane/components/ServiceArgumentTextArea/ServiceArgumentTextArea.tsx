// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { TextAreaInput } from "@intel-enterprise-rag-ui/components";
import { formatSnakeCaseToTitleCase } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler } from "react";

export type ServiceArgumentTextAreaValue = string;

interface ServiceArgumentTextAreaProps {
  value: string;
  placeholder: string;
  isInvalid: boolean;
  rows?: number;
  titleCaseLabel?: boolean;
  inputConfig: {
    name: string;
    tooltipText?: string;
  };
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
}

const ServiceArgumentTextArea = ({
  value,
  placeholder,
  isInvalid,
  rows = 3,
  titleCaseLabel = true,
  inputConfig: { name, tooltipText },
  onChange,
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
