// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppNameText.scss";

interface AppNameProps {
  /** Application name to display */
  appName: string;
}

/**
 * Displays application name.
 */
export const AppNameText = ({ appName }: AppNameProps) => (
  <p className="app-name__text">{appName}</p>
);
