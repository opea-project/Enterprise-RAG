// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./UsernameText.scss";

interface UsernameProps {
  /** Username to display */
  username: string;
}

/**
 * Displays username.
 */
export const UsernameText = ({ username }: UsernameProps) => (
  <p className="username__text">{username}</p>
);
