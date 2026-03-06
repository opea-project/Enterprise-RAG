// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceData } from "@/types/index";

export interface ControlPlaneCardProps {
  data: ServiceData;
  changeArguments: (request: { name: string; data: unknown }[]) => void; // TODO: Replace with RTK Query mutation once API is moved to the control plane package
}
