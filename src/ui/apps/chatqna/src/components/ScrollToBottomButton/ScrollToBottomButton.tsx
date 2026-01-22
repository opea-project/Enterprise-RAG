// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScrollToBottomButton.scss";

import {
  IconButton,
  IconButtonProps,
} from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";

interface ScrollToBottomButtonProps
  extends Omit<IconButtonProps, "color" | "icon"> {
  show: boolean;
}

const ScrollToBottomButton = ({
  show,
  className,
  ...rest
}: ScrollToBottomButtonProps) => (
  <IconButton
    {...rest}
    icon="scroll-to-bottom"
    aria-label="Scroll to bottom"
    className={classNames([
      {
        visible: show,
        invisible: !show,
      },
      "scroll-to-bottom-button",
      className,
    ])}
  />
);

export default ScrollToBottomButton;
