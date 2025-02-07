// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Tooltip.scss";

import { PropsWithChildren, ReactNode, useState } from "react";

export type TooltipPosition =
  | "top"
  | "bottom"
  | "left"
  | "right"
  | "bottom-start"
  | "bottom-end"
  | "bottom-right";

interface TooltipProps extends PropsWithChildren {
  position?: TooltipPosition;
  text: string | ReactNode;
}

const Tooltip = ({ children, text, position = "bottom" }: TooltipProps) => {
  const [visible, setVisible] = useState(false);

  const showTooltip = () => {
    setVisible(true);
  };

  const hideTooltip = () => {
    setVisible(false);
  };

  return (
    <div
      className="tooltip-wrapper"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}
      {visible && <div className={`tooltip ${position}`}>{text}</div>}
    </div>
  );
};

export default Tooltip;
