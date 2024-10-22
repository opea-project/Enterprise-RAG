// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Tooltip.scss";

import { PropsWithChildren, useState } from "react";

type TooltipPosition =
  | "top"
  | "bottom"
  | "left"
  | "right"
  | "bottom-start"
  | "bottom-end";

interface TooltipProps extends PropsWithChildren {
  position?: TooltipPosition;
  text: string;
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
