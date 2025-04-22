// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScrollToBottomButton.scss";

import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";

import IconButton from "@/components/ui/IconButton/IconButton";

interface ScrollToBottomButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "color"> {
  show: boolean;
}

const ScrollToBottomButton = ({
  show,
  ...props
}: ScrollToBottomButtonProps) => (
  <IconButton
    icon="scroll-to-bottom"
    className={classNames([
      {
        visible: show,
        invisible: !show,
      },
      "scroll-to-bottom-button",
    ])}
    {...props}
  />
);

export default ScrollToBottomButton;
