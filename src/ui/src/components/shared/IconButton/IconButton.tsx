// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./IconButton.scss";

import classNames from "classnames";
import { ButtonHTMLAttributes, ReactNode } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ReactNode;
}

const IconButton = ({ icon, className, ...props }: IconButtonProps) => (
  <button className={classNames("icon-button", className)} {...props}>
    {icon}
  </button>
);

export default IconButton;
