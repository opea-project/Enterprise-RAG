// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./NavigationItem.scss";

import { Typography } from "@mui/material";
import { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const convertPathToLabel = (path: string) => {
  let label = path.replace("/", "");
  label = label
    .split("-")
    .map((value) => value[0].toUpperCase() + value.slice(1))
    .join(" ");
  return label;
};

interface NavigationItemProps {
  path: string;
  icon: ReactNode;
}

const NavigationItem = ({ path, icon }: NavigationItemProps) => (
  <NavLink to={path} className="nav-item">
    {icon}
    <Typography
      variant="navigation-item-label"
      align="center"
      className="nav-item-label"
    >
      {convertPathToLabel(path)}
    </Typography>
  </NavLink>
);

export default NavigationItem;
