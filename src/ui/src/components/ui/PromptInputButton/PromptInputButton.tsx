// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import { IconName } from "@/components/icons";
import IconButton, {
  IconButtonProps,
} from "@/components/ui/IconButton/IconButton";

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
