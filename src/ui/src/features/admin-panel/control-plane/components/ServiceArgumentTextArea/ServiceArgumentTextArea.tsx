// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { ChangeEventHandler } from "react";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
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
  const textareaClassNames = classNames([
    { "input--invalid": isInvalid },
    "w-full p-2",
  ]);

  const labelText = formatSnakeCaseToTitleCase(name);

  return (
    <div className="grid grid-rows-[1.5rem_1fr]">
      <label
        htmlFor={name}
        className="flex flex-row items-center gap-1 text-xs"
      >
        <Tooltip title={tooltipText} trigger={<InfoIcon />} placement="left" />
        <span>{labelText}</span>
      </label>
      <textarea
        value={value}
        name={name}
        placeholder={placeholder}
        className={textareaClassNames}
        onChange={onChange}
      />
    </div>
  );
};

export default ServiceArgumentTextArea;
