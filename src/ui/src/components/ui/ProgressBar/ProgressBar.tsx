// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ProgressBar.scss";

import {
  ProgressBar as AriaProgressBar,
  ProgressBarProps,
} from "react-aria-components";

const ProgressBar = (props: ProgressBarProps) => (
  <AriaProgressBar {...props} className="progress-bar">
    {({ percentage }) => (
      <div className="progress-bar__bar">
        <div
          className="progress-bar__bar__fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    )}
  </AriaProgressBar>
);

export default ProgressBar;
