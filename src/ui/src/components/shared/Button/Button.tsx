// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Button.scss";

import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";

import { IconName, icons } from "@/components/icons";

type ButtonColors = "primary" | "error" | "success";
type ButtonSizes = "sm";
type ButtonVariants = "outlined";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  color?: ButtonColors;
  size?: ButtonSizes;
  variant?: ButtonVariants;
  fullWidth?: boolean;
  icon?: IconName;
}

const Button = ({
  color = "primary",
  size,
  variant,
  fullWidth,
  icon,
  className,
  children,
  ...props
}: ButtonProps) => {
  const buttonClassNames = classNames([
    {
      "button--sm": size === "sm",
      "button--success": color === "success",
      "button--error": color === "error",
      "button--outlined": variant === "outlined",
      "button--outlined-primary": variant === "outlined" && color === "primary",
      "button--outlined-error": variant === "outlined" && color === "error",
      "button--with-icon": icon,
      "w-full": fullWidth,
    },
    className,
  ]);

  let content = children;
  if (icon) {
    const IconComponent = icons[icon];
    content = (
      <>
        <IconComponent />
        {children}
      </>
    );
  }

  return (
    <button className={buttonClassNames} {...props}>
      {content}
    </button>
  );
};

export default Button;
