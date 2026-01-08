// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./IconButton.scss";

import { IconName, icons } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { forwardRef } from "react";
import {
  Button as AriaButton,
  ButtonProps as AriaButtonProps,
} from "react-aria-components";

type IconButtonVariants = "outlined" | "contained";
type IconButtonSizes = "sm" | "md";
export type IconButtonColor = "primary" | "error" | "success";

export interface IconButtonProps extends AriaButtonProps {
  /** Name of the icon to display */
  icon: IconName;
  /** Color of the button (primary, error, success) */
  color?: IconButtonColor;
  /** Size of the button (small, medium) */
  size?: IconButtonSizes;
  /** Variant of the button (outlined, contained) */
  variant?: IconButtonVariants;
  /** Test identifier for automated testing */
  "data-testid"?: string;
}

/**
 * Icon button component for actions represented by icons, supporting color, size, and variant options.
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    { icon, color = "primary", size = "md", variant, className, ...rest },
    ref,
  ) => {
    const iconButtonClassNames = classNames(
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
    );

    const IconComponent = icons[icon];

    return (
      <AriaButton {...rest} ref={ref} className={iconButtonClassNames}>
        <IconComponent />
      </AriaButton>
    );
  },
);

IconButton.displayName = "IconButton";
