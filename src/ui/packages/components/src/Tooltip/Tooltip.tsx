// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Tooltip.scss";

import { ReactNode } from "react";
import {
  Focusable as AriaFocusable,
  Tooltip as AriaTooltip,
  TooltipProps as AriaTooltipProps,
  TooltipTrigger as AriaTooltipTrigger,
} from "react-aria-components";

interface TooltipProps extends Omit<AriaTooltipProps, "children"> {
  /** Tooltip text to display */
  title: string;
  /** Element that triggers the tooltip */
  trigger: ReactNode;
}

/**
 * Tooltip component for displaying contextual information on hover or focus.
 */
export const Tooltip = ({ trigger, title, ...rest }: TooltipProps) => (
  <AriaTooltipTrigger delay={200} closeDelay={200}>
    <AriaFocusable>
      <span role="button" tabIndex={-1}>
        {trigger}
      </span>
    </AriaFocusable>
    <AriaTooltip {...rest} offset={8} className="tooltip">
      {title}
    </AriaTooltip>
  </AriaTooltipTrigger>
);
