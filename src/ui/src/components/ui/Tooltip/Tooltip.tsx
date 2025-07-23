// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Tooltip.scss";

import { ReactNode } from "react";
import {
  Focusable,
  Tooltip as ReactAriaTooltip,
  TooltipProps as ReactAriaTooltipProps,
  TooltipTrigger,
} from "react-aria-components";

interface TooltipProps extends Omit<ReactAriaTooltipProps, "children"> {
  title: string;
  trigger: ReactNode;
}

const Tooltip = ({ trigger, title, ...rest }: TooltipProps) => (
  <TooltipTrigger delay={200} closeDelay={200}>
    <Focusable>
      <span role="button" tabIndex={-1}>
        {trigger}
      </span>
    </Focusable>
    <ReactAriaTooltip {...rest} offset={8} className="tooltip">
      {title}
    </ReactAriaTooltip>
  </TooltipTrigger>
);

export default Tooltip;
