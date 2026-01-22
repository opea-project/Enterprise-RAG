// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Menu.scss";

import { PropsWithChildren, ReactNode } from "react";
import {
  Menu as AriaMenu,
  MenuItem as AriaMenuItem,
  MenuItemProps as AriaMenuItemProps,
  MenuProps as AriaMenuProps,
  MenuTrigger as AriaMenuTrigger,
  MenuTriggerProps as AriaMenuTriggerProps,
} from "react-aria-components";

import { Popover, PopoverProps } from "@/Popover/Popover";

/**
 * Menu component for rendering a list of selectable actions or options.
 */
const Menu = <T extends object>({ children, ...rest }: AriaMenuProps<T>) => (
  <AriaMenu {...rest}>{children}</AriaMenu>
);

/**
 * Menu item component for individual selectable option in a menu.
 */
const MenuItem = ({ className, children, ...rest }: AriaMenuItemProps) => (
  <AriaMenuItem className={`menu-item ${className}`} {...rest}>
    {children}
  </AriaMenuItem>
);

interface MenuTriggerProps
  extends Omit<AriaMenuTriggerProps, "children" | "trigger">,
    PropsWithChildren {
  /** Element that triggers the menu */
  trigger: ReactNode;
  /** Accessible label for the menu */
  ariaLabel?: string;
  /** Placement of the menu popover */
  placement?: PopoverProps["placement"];
  /** Content to display inside the menu */
  children: ReactNode;
}

/**
 * Menu trigger component for opening a menu via a trigger element.
 */
const MenuTrigger = ({
  trigger,
  ariaLabel = "Menu",
  placement = "bottom start",
  children,
  ...rest
}: MenuTriggerProps) => (
  <AriaMenuTrigger {...rest}>
    {trigger}
    <Popover ariaLabel={ariaLabel} placement={placement}>
      {children}
    </Popover>
  </AriaMenuTrigger>
);

export { Menu, MenuItem, MenuTrigger };
