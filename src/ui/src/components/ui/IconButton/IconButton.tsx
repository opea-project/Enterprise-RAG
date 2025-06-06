// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./IconButton.scss";

import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";

import { IconName, icons } from "@/components/icons";

type IconButtonVariants = "outlined" | "contained";
type IconButtonSizes = "sm";
export type IconButtonColor = "primary" | "error" | "success";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: IconName;
  color?: IconButtonColor;
  size?: IconButtonSizes;
  variant?: IconButtonVariants;
}

const IconButton = ({
  icon,
  color = "primary",
  size,
  variant,
  className,
  ...props
}: IconButtonProps) => {
  const iconButtonClassNames = classNames([
    "icon-button",
    {
      "icon-button--error": !variant && color === "error",
      "icon-button--success": !variant && color === "success",
      "icon-button--sm": size === "sm",
      "icon-button--outlined": variant === "outlined",
      "icon-button--contained": variant === "contained",
      "icon-button--outlined-primary":
        variant === "outlined" && color === "primary",
      "icon-button--outlined-error":
        variant === "outlined" && color === "error",
      "icon-button--outlined-success":
        variant === "outlined" && color === "success",
    },
    className,
  ]);

  const IconComponent = icons[icon];

  return (
    <button className={iconButtonClassNames} {...props}>
      <IconComponent />
    </button>
  );
};

export default IconButton;
