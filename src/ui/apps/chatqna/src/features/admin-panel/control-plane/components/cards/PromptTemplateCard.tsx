// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getValidationErrorMessage } from "@intel-enterprise-rag-ui/input-validation";
import { sanitizeString } from "@intel-enterprise-rag-ui/utils";
import { ChangeEventHandler, useEffect, useState } from "react";

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";
import ServiceArgumentTextArea from "@/features/admin-panel/control-plane/components/ServiceArgumentTextArea/ServiceArgumentTextArea";
import {
  PromptTemplateArgs,
  promptTemplateFormConfig,
} from "@/features/admin-panel/control-plane/config/chat-qna-graph/promptTemplate";
import useServiceCard from "@/features/admin-panel/control-plane/hooks/useServiceCard";
import { validatePromptTemplateForm } from "@/features/admin-panel/control-plane/validators/promptTemplateInput";

const PromptTemplateCard = ({
  data: {
    id,
    status,
    displayName,
    promptTemplateArgs: prevPromptTemplateArguments,
  },
}: ControlPlaneCardProps) => {
  const {
    argumentsForm: promptTemplateForm,
    onArgumentValueChange,
    footerProps,
  } = useServiceCard<PromptTemplateArgs>(id, prevPromptTemplateArguments);

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
  }, [promptTemplateForm, isHydrated]);

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
      <div className="grid h-full grid-rows-[1fr_1fr_auto] gap-4 pt-4 text-xs">
        <ServiceArgumentTextArea
          value={promptTemplateForm.system_prompt_template ?? ""}
          placeholder="Enter system prompt template..."
          isInvalid={showInvalid}
          inputConfig={promptTemplateFormConfig.system_prompt_template}
          onChange={handleChange}
        />
        <ServiceArgumentTextArea
          value={promptTemplateForm.user_prompt_template ?? ""}
          placeholder="Enter user prompt template..."
          isInvalid={showInvalid}
          inputConfig={promptTemplateFormConfig.user_prompt_template}
          onChange={handleChange}
        />
        <div>
          <p className="error mb-3 min-h-14 text-xs italic">{error}</p>
        </div>
      </div>
    </SelectedServiceCard>
  );
};

export default PromptTemplateCard;
