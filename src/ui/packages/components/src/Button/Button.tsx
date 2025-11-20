// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Button.scss";

import { IconName, icons } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { forwardRef } from "react";
import {
  Button as AriaButton,
  ButtonProps as AriaButtonProps,
} from "react-aria-components";

export type ButtonColor = "primary" | "error" | "success";
type ButtonSize = "sm";
type ButtonVariant = "outlined" | "text";

interface ButtonProps extends AriaButtonProps {
  /** Color of the button (primary, error, success) */
  color?: ButtonColor;
  /** Size of the button (small) */
  size?: ButtonSize;
  /** Variant of the button (outlined, text) */
  variant?: ButtonVariant;
  /** If true, button takes full width */
  fullWidth?: boolean;
  /** Name of the icon to display */
  icon?: IconName;
}

/**
 * Button component for user actions, supporting color, size, variant, icon, and full width options.
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
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
        "button--full-width": fullWidth,
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
      <AriaButton {...rest} ref={ref} className={buttonClassNames}>
        {content}
      </AriaButton>
    );
  },
);

Button.displayName = "Button";
