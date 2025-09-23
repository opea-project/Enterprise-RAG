// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import {
  IconButton,
  IconButtonProps,
} from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";

interface PromptInputButtonProps extends Omit<IconButtonProps, "color"> {
  icon: IconName;
}

const PromptInputButton = ({
  icon,
  className,
  ...rest
}: PromptInputButtonProps) => (
  <IconButton
    {...rest}
    icon={icon}
    className={`prompt-input__button ${className}`}
  />
);

export default PromptInputButton;
