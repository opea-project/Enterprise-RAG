// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import classNames from "classnames";
import { ChangeEventHandler, useState } from "react";
import { ValidationError } from "yup";

import Button from "@/components/ui/Button/Button";
import { useChangeArgumentsMutation } from "@/features/admin-panel/control-plane/api";
import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import { ChangeArgumentsRequest } from "@/features/admin-panel/control-plane/types/api";
import { validatePromptTemplateInput } from "@/features/admin-panel/control-plane/validators/promptTemplateInput";
import { sanitizeString } from "@/utils";

const PromptTemplateCard = ({
  data: { status, displayName, promptTemplate: defaultPromptTemplate },
}: ControlPlaneCardProps) => {
  const [changeArguments] = useChangeArgumentsMutation();

  const [promptTemplate, setPromptTemplate] = useState<string>(
    defaultPromptTemplate || "",
  );
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");

  const validateInput = async (value: string) => {
    try {
      await validatePromptTemplateInput(value);
      setIsInvalid(false);
      setError("");
      return true;
    } catch (validationError) {
      setIsInvalid(true);
      setError((validationError as ValidationError).message);
      return false;
    }
  };

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = async (
    event,
  ) => {
    const newValue = event.target.value;
    setPromptTemplate(newValue);
    const sanitizedValue = sanitizeString(newValue);
    const isValid = await validateInput(sanitizedValue);
    setIsInvalid(!isValid);
  };

  const handleChangePromptTemplateBtnClick = () => {
    const changeArgumentsRequest: ChangeArgumentsRequest = [
      {
        name: "prompt_template",
        data: {
          prompt_template: promptTemplate,
        },
      },
    ];

    changeArguments(changeArgumentsRequest);
  };

  const textareaClassNames = classNames([
    {
      "input--invalid": isInvalid,
    },
    "w-full text-xs mt-4 mb-0 p-2 h-[calc(100%-5.75rem)]",
  ]);

  const changePromptTemplateBtnDisabled =
    isInvalid || promptTemplate === defaultPromptTemplate;

  return (
    <SelectedServiceCard serviceStatus={status} serviceName={displayName}>
      <textarea
        value={promptTemplate}
        name="prompt-template-input"
        placeholder="Enter your prompt template..."
        className={textareaClassNames}
        onChange={handleChange}
      />
      <p className="error mb-2 mt-[0.25rem] text-xs italic">{error}</p>
      <Button
        size="sm"
        disabled={changePromptTemplateBtnDisabled}
        fullWidth
        onClick={handleChangePromptTemplateBtnClick}
      >
        Change Prompt Template
      </Button>
    </SelectedServiceCard>
  );
};

export default PromptTemplateCard;
