// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScrollToBottomButton.scss";

import classNames from "classnames";

import IconButton, {
  IconButtonProps,
} from "@/components/ui/IconButton/IconButton";

interface ScrollToBottomButtonProps
  extends Omit<IconButtonProps, "color" | "icon"> {
  show: boolean;
}

const ScrollToBottomButton = ({
  show,
  ...props
}: ScrollToBottomButtonProps) => (
  <IconButton
    {...props}
    icon="scroll-to-bottom"
    aria-label="Scroll to bottom"
    className={classNames([
      {
        visible: show,
        invisible: !show,
      },
      "scroll-to-bottom-button",
    ])}
  />
);

export default ScrollToBottomButton;
