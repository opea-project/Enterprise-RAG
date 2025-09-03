// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ChangeEventHandler,
  FormEventHandler,
  useEffect,
  useState,
} from "react";
import { ValidationError } from "yup";

import Button from "@/components/ui/Button/Button";
import { useChangeArgumentsMutation } from "@/features/admin-panel/control-plane/api";
import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentTextArea from "@/features/admin-panel/control-plane/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
import {
  PromptTemplateArgs,
  promptTemplateFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/prompt-template";
import { ChangeArgumentsRequest } from "@/features/admin-panel/control-plane/types/api";
import { validatePromptTemplateForm } from "@/features/admin-panel/control-plane/validators/promptTemplateInput";
import { sanitizeString } from "@/utils";

const PromptTemplateCard = ({
  data: {
    status,
    displayName,
    promptTemplateArgs: prevPromptTemplateArguments,
  },
}: ControlPlaneCardProps) => {
  const [changeArguments] = useChangeArgumentsMutation();

  const [promptTemplateForm, setPromptTemplateForm] =
    useState<PromptTemplateArgs>(
      (prevPromptTemplateArguments ??
        ({} as PromptTemplateArgs)) as PromptTemplateArgs,
    );

  const [isHydrated, setIsHydrated] = useState<boolean>(
    !!prevPromptTemplateArguments,
  );
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");
  const showInvalid = isInvalid && isHydrated;

  useEffect(() => {
    if (prevPromptTemplateArguments !== undefined) {
      setPromptTemplateForm(prevPromptTemplateArguments);
      setIsHydrated(true);
    } else {
      setIsHydrated(false);
    }
  }, [prevPromptTemplateArguments]);

  useEffect(() => {
    if (!isHydrated) {
      setIsInvalid(false);
      setError("");
      return;
    }
    const validateForm = async () => {
      try {
        await validatePromptTemplateForm(promptTemplateForm);
        setIsInvalid(false);
        setError("");
      } catch (validationError) {
        setIsInvalid(true);
        setError((validationError as ValidationError).message);
      }
    };

    validateForm();
  }, [promptTemplateForm, isHydrated]);

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    const { value, name } = event.target;
    setPromptTemplateForm((prevForm) => ({
      ...prevForm,
      [name]: sanitizeString(value),
    }));
  };

  const handlePromptTemplateArgsSubmit: FormEventHandler<HTMLFormElement> = (
    event,
  ) => {
    event.preventDefault();
    const changeArgumentsRequest: ChangeArgumentsRequest = [
      {
        name: "prompt_template",
        data: promptTemplateForm,
      },
    ];

    changeArguments(changeArgumentsRequest);
  };

  const changePromptTemplateBtnDisabled =
    !isHydrated ||
    isInvalid ||
    (promptTemplateForm.user_prompt_template ===
      prevPromptTemplateArguments?.user_prompt_template &&
      promptTemplateForm.system_prompt_template ===
        prevPromptTemplateArguments?.system_prompt_template);

  return (
    <SelectedServiceCard serviceStatus={status} serviceName={displayName}>
      <form
        className="grid h-full grid-rows-[1fr_1fr_auto] gap-4 pt-4 text-xs"
        onSubmit={handlePromptTemplateArgsSubmit}
      >
        <ServiceArgumentTextArea
          value={promptTemplateForm.system_prompt_template ?? ""}
          placeholder="Enter system prompt template..."
          isInvalid={showInvalid}
          onChange={handleChange}
          inputConfig={promptTemplateFormConfig.system_prompt_template}
        />
        <ServiceArgumentTextArea
          value={promptTemplateForm.user_prompt_template ?? ""}
          placeholder="Enter user prompt template..."
          isInvalid={showInvalid}
          onChange={handleChange}
          inputConfig={promptTemplateFormConfig.user_prompt_template}
        />
        <div>
          <p className="error mb-3 min-h-14 text-xs italic">{error}</p>
          <Button
            size="sm"
            type="submit"
            isDisabled={changePromptTemplateBtnDisabled}
            fullWidth
          >
            Change Prompt Template
          </Button>
        </div>
      </form>
    </SelectedServiceCard>
  );
};

export default PromptTemplateCard;
