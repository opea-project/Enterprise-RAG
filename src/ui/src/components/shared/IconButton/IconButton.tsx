// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./IconButton.scss";

import { Icon } from "@iconify/react";
import classNames from "classnames";

interface IconButtonProps {
  className?: string;
  icon: string;
  disabled?: boolean;
  onClick: () => void;
}

const IconButton = ({
  icon,
  disabled,
  className,
  onClick,
}: IconButtonProps) => (
  <button
    className={classNames("icon-button", className)}
    disabled={disabled}
    onClick={onClick}
  >
    <Icon icon={icon} />
  </button>
);

export default IconButton;
