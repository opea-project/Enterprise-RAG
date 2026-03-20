// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptTemplateCard.scss";

import { getValidationErrorMessage } from "@intel-enterprise-rag-ui/input-validation";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useEffect, useState } from "react";

import { SelectedServiceCard } from "@/components/SelectedServiceCard/SelectedServiceCard";
import { ServiceArgumentTextArea } from "@/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
import {
  PromptTemplateArgs,
  promptTemplateFormConfig,
} from "@/configs/services/promptTemplate";
import { useServiceCard } from "@/hooks/useServiceCard";
import { ControlPlaneCardProps } from "@/types/cards";

export interface PromptTemplateCardProps extends ControlPlaneCardProps {
  validatePromptTemplateForm: (templates: PromptTemplateArgs) => Promise<void>;
}

export const PromptTemplateCard = ({
  data: {
    id,
    status,
    displayName,
    promptTemplateArgs: prevPromptTemplateArguments,
  },
  changeArguments,
  validatePromptTemplateForm,
}: PromptTemplateCardProps) => {
  const config = promptTemplateFormConfig;

  const {
    argumentsForm: promptTemplateForm,
    onArgumentValueChange,
    footerProps,
  } = useServiceCard<PromptTemplateArgs>(id, prevPromptTemplateArguments, {
    changeArguments,
  });

  const [isHydrated, setIsHydrated] = useState<boolean>(
    !!prevPromptTemplateArguments,
  );
  const [isInvalid, setIsInvalid] = useState(false);
  const [error, setError] = useState("");
  const showInvalid = isInvalid && isHydrated;

  useEffect(() => {
    if (prevPromptTemplateArguments !== undefined) {
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
        setError(getValidationErrorMessage(validationError));
      }
    };

    validateForm();
  }, [promptTemplateForm, isHydrated, validatePromptTemplateForm]);

  const handleChange: ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    const { value, name } = event.target;
    onArgumentValueChange(name, sanitizeString(value));
  };

  return (
    <SelectedServiceCard
      serviceStatus={status}
      serviceName={displayName}
      footerProps={{
        ...footerProps,
        isConfirmChangesButtonDisabled:
          footerProps.isConfirmChangesButtonDisabled || isInvalid,
      }}
    >
      <div className="form-container">
        <ServiceArgumentTextArea
          value={promptTemplateForm.system_prompt_template ?? ""}
          placeholder="Enter system prompt template..."
          isInvalid={showInvalid}
          inputConfig={config.system_prompt_template}
          onChange={handleChange}
        />
        <ServiceArgumentTextArea
          value={promptTemplateForm.user_prompt_template ?? ""}
          placeholder="Enter user prompt template..."
          isInvalid={showInvalid}
          inputConfig={config.user_prompt_template}
          onChange={handleChange}
        />
        <div>
          <p className="error error-message">{error}</p>
        </div>
      </div>
    </SelectedServiceCard>
  );
};
