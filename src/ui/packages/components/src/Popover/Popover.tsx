// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Popover.scss";

import { ReactNode } from "react";
import {
  Dialog as AriaDialog,
  Popover as AriaPopover,
  PopoverProps as AriaPopoverProps,
} from "react-aria-components";

interface PopoverProps extends AriaPopoverProps {
  /** Accessible label for the popover dialog */
  ariaLabel?: string;
  /** Content to display inside the popover */
  children: ReactNode;
}

/**
 * Popover component for displaying content in a floating dialog.
 */
export const Popover = ({ ariaLabel, children, ...rest }: PopoverProps) => (
  <AriaPopover {...rest} className="popover !z-[101]">
    <AriaDialog aria-label={ariaLabel}>{children}</AriaDialog>
  </AriaPopover>
);
