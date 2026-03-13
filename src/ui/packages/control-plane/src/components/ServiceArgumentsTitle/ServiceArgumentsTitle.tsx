// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentsTitle.scss";

import { PropsWithChildren } from "react";

/**
 * Title component for service arguments sections in card components
 */
export const ServiceArgumentsTitle = ({ children }: PropsWithChildren) => (
  <p className="service-arguments-title">{children}</p>
);
