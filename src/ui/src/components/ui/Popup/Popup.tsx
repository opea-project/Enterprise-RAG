// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from "react";
import {
  Dialog,
  DialogTrigger,
  Popover,
  PopoverProps,
  Pressable,
} from "react-aria-components";

interface PopupProps extends PopoverProps {
  popupTrigger: JSX.Element;
  children: ReactNode;
}

const Popup = ({ popupTrigger, children, ...restProps }: PopupProps) => (
  <DialogTrigger>
    <Pressable>{popupTrigger}</Pressable>
    <Popover {...restProps}>
      <Dialog>{children}</Dialog>
    </Popover>
  </DialogTrigger>
);

export default Popup;
