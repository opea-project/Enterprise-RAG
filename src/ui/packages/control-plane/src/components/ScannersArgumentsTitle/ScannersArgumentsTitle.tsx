// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScannersArgumentsTitle.scss";

import { PropsWithChildren } from "react";

/**
 * Title component for scanner arguments sections in guard card components
 */
export const ScannersArgumentsTitle = ({ children }: PropsWithChildren) => (
  <p className="scanners-arguments-title">{children}</p>
);
