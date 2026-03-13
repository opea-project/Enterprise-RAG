// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ScannerInputsTitle.scss";

import { PropsWithChildren } from "react";

/**
 * Title component for individual scanner input sections
 */
export const ScannerInputsTitle = ({ children }: PropsWithChildren) => (
  <p className="scanner-inputs-title">{children}</p>
);
