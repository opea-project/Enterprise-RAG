// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Button.scss";

import classNames from "classnames";
import { forwardRef } from "react";
import {
  Button as ReactAriaButton,
  ButtonProps as ReactAriaButtonProps,
} from "react-aria-components";

import { IconName, icons } from "@/components/icons";

export type ButtonColor = "primary" | "error" | "success";
type ButtonSize = "sm";
type ButtonVariant = "outlined" | "text";

interface ButtonProps extends ReactAriaButtonProps {
  color?: ButtonColor;
  size?: ButtonSize;
  variant?: ButtonVariant;
  fullWidth?: boolean;
  icon?: IconName;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      color = "primary",
      size,
      variant,
      fullWidth,
      icon,
      className,
      children,
      ...rest
    },
    ref,
  ) => {
    const buttonClassNames = classNames("button", [
      {
        "button--sm": size === "sm",
        "button--success": color === "success",
        "button--error": color === "error",
        "button--outlined": variant === "outlined",
        "button--text": variant === "text",
        "button--outlined-primary":
          variant === "outlined" && color === "primary",
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
      <ReactAriaButton {...rest} ref={ref} className={buttonClassNames}>
        {content}
      </ReactAriaButton>
    );
  },
);

export default Button;
