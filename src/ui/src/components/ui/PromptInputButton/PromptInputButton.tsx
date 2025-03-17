// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import { ButtonHTMLAttributes } from "react";

import { IconName } from "@/components/icons";
import IconButton from "@/components/ui/IconButton/IconButton";

interface PromptInputButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "color"> {
  icon: IconName;
}

const PromptInputButton = ({ icon, ...props }: PromptInputButtonProps) => (
  <IconButton icon={icon} className="prompt-input__button" {...props} />
);

export default PromptInputButton;
