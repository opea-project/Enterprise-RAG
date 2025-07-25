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

import Popover from "@/components/ui/Popover/Popover";

const Menu = <T extends object>({ children, ...rest }: AriaMenuProps<T>) => (
  <AriaMenu {...rest}>{children}</AriaMenu>
);

const MenuItem = ({ className, children, ...rest }: AriaMenuItemProps) => (
  <AriaMenuItem className={`menu-item ${className}`} {...rest}>
    {children}
  </AriaMenuItem>
);

interface MenuTriggerProps
  extends Omit<AriaMenuTriggerProps, "children" | "trigger">,
    PropsWithChildren {
  trigger: ReactNode;
  ariaLabel?: string;
  children: ReactNode;
}

const MenuTrigger = ({
  trigger,
  ariaLabel = "Menu",
  children,
  ...rest
}: MenuTriggerProps) => (
  <AriaMenuTrigger {...rest}>
    {trigger}
    <Popover ariaLabel={ariaLabel}>{children}</Popover>
  </AriaMenuTrigger>
);

export { Menu, MenuItem, MenuTrigger };
