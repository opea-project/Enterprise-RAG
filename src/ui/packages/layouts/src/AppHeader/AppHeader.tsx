// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AppHeader.scss";

import { ReactNode } from "react";

export interface AppHeaderProps {
  /** Content to display on the left side of the header */
  leftSideContent?: ReactNode;
  /** Content to display on the right side of the header */
  rightSideContent?: ReactNode;
}

/**
 * Application header component for layout structure.
 * Displays customizable left and right content areas.
 */
export const AppHeader = ({
  leftSideContent,
  rightSideContent,
}: AppHeaderProps) => (
  <header className="app-header">
    <div className="app-header__actions">{leftSideContent}</div>
    <div className="app-header__actions">{rightSideContent}</div>
  </header>
);
