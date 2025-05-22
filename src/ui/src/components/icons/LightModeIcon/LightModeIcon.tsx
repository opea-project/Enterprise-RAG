// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconBaseProps } from "react-icons";
import { PiSunFill } from "react-icons/pi";

const LightModeIcon = ({ className, ...props }: IconBaseProps) => (
  <PiSunFill
    {...props}
    className={`text-base text-light-text-accent ${className}`}
  />
);

export default LightModeIcon;
