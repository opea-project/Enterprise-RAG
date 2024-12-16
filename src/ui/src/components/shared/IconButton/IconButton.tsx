// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./IconButton.scss";

import { Icon } from "@iconify/react";
import classNames from "classnames";
import { ButtonHTMLAttributes } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: string;
}

const IconButton = ({ icon, className, ...props }: IconButtonProps) => (
  <button className={classNames("icon-button", className)} {...props}>
    <Icon icon={icon} />
  </button>
);

export default IconButton;
