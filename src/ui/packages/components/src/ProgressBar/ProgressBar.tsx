// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ProgressBar.scss";

import {
  ProgressBar as AriaProgressBar,
  ProgressBarProps as AriaProgressBarProps,
} from "react-aria-components";

/**
 * Progress bar component for visualizing completion percentage.
 */
export const ProgressBar = (props: AriaProgressBarProps) => (
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
