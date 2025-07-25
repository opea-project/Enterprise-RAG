// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Switch.scss";

import {
  Switch as AriaSwitch,
  SwitchProps as AriaSwitchProps,
} from "react-aria-components";

const Switch = ({ className, ...rest }: AriaSwitchProps) => (
  <AriaSwitch {...rest} className={`switch ${className}`}>
    <div className="switch__indicator" />
  </AriaSwitch>
);

export default Switch;
