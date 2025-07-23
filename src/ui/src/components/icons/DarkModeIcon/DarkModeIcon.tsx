// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconBaseProps } from "react-icons";
import { PiMoonStarsFill } from "react-icons/pi";

const DarkModeIcon = ({ className, ...rest }: IconBaseProps) => (
  <PiMoonStarsFill
    {...rest}
    className={`text-base text-dark-text-inverse ${className}`}
  />
);

export default DarkModeIcon;
