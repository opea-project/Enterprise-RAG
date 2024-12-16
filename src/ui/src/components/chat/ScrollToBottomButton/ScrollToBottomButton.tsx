// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScrollToBottomButton.scss";

import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";

import IconButton from "@/components/shared/IconButton/IconButton";

interface ScrollToBottomButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  show: boolean;
}

const ScrollToBottomButton = ({
  show,
  ...props
}: ScrollToBottomButtonProps) => (
  <IconButton
    icon="tabler:chevron-down"
    className={classNames({
      "scroll-to-bottom-button": true,
      visible: show,
      invisible: !show,
    })}
    {...props}
  />
);

export default ScrollToBottomButton;
