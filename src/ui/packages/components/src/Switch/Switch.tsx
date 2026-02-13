// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Switch.scss";

import {
  Switch as AriaSwitch,
  SwitchProps as AriaSwitchProps,
} from "react-aria-components";

/**
 * Switch component for toggling between on/off states.
 */
export const Switch = ({ className, ...rest }: AriaSwitchProps) => (
  <AriaSwitch {...rest} className={`switch ${className}`}>
    <div className="switch__indicator" />
  </AriaSwitch>
);
