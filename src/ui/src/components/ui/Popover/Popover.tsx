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
  ariaLabel?: string;
  children: ReactNode;
}

const Popover = ({ ariaLabel, children, ...rest }: PopoverProps) => (
  <AriaPopover {...rest} className="popover !z-20">
    <AriaDialog aria-label={ariaLabel}>{children}</AriaDialog>
  </AriaPopover>
);

export default Popover;
