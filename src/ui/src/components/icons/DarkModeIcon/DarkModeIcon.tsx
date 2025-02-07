// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconBaseProps } from "react-icons";
import { PiMoonStarsFill } from "react-icons/pi";

const DarkModeIcon = ({ className, ...props }: IconBaseProps) => (
  <PiMoonStarsFill
    className={`text-base text-dark-text-inverse ${className}`}
    {...props}
  />
);

export default DarkModeIcon;
