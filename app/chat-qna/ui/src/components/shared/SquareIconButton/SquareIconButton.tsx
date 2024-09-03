// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SquareIconButton.scss";

import { Button, ButtonProps } from "@mui/material";
import { PropsWithChildren } from "react";

interface SquareIconButtonProps extends PropsWithChildren, ButtonProps {}

const SquareIconButton = ({
  children,
  color = "primary",
  disabled,
  onClick,
}: SquareIconButtonProps) => (
  <Button
    color={color}
    disabled={disabled}
    disableRipple
    variant="outlined"
    onClick={onClick}
    className={`square-icon-button ${color}`}
  >
    {children}
  </Button>
);

export default SquareIconButton;
