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
  onChange: ChangeEventHandler<HTMLTextAreaElement>;
  inputConfig: {
    name: string;
    tooltipText: string;
  };
}

const ServiceArgumentTextArea = ({
  value,
  placeholder,
  isInvalid,
  onChange,
  inputConfig: { name, tooltipText },
}: ServiceArgumentTextAreaProps) => {
  const label = formatSnakeCaseToTitleCase(name);

  return (
    <TextAreaInput
      name={name}
      value={value}
      label={label}
      size="sm"
      placeholder={placeholder}
      isInvalid={isInvalid}
      tooltipText={tooltipText}
      onChange={onChange}
    />
  );
};

export default ServiceArgumentTextArea;
