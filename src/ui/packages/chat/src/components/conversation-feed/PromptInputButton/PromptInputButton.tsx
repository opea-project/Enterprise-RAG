// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PromptInputButton.scss";

import {
  IconButton,
  IconButtonProps,
} from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";

interface PromptInputButtonProps extends Omit<IconButtonProps, "color"> {
  icon: IconName;
}

export const PromptInputButton = ({
  icon,
  className,
  ...rest
}: PromptInputButtonProps) => (
  <IconButton
    {...rest}
    icon={icon}
    className={classNames("prompt-input__button", className)}
  />
);
