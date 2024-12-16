// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import { ButtonHTMLAttributes } from "react";

import IconButton from "@/components/shared/IconButton/IconButton";

interface PromptInputButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: string;
}

const PromptInputButton = ({ icon, ...props }: PromptInputButtonProps) => (
  <IconButton icon={icon} className="prompt-input__button" {...props} />
);

export default PromptInputButton;
