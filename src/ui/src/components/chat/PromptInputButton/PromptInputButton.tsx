// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import IconButton from "@/components/shared/IconButton/IconButton";

interface PromptInputButtonProps {
  icon: string;
  disabled?: boolean;
  onClick: () => void;
}

const PromptInputButton = ({
  disabled,
  onClick,
  icon,
}: PromptInputButtonProps) => (
  <IconButton
    className="prompt-input__button"
    icon={icon}
    disabled={disabled}
    onClick={onClick}
  />
);

export default PromptInputButton;
