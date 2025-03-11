// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/features/admin-panel/control-plane/components/cards";
import SelectedServiceCard from "@/features/admin-panel/control-plane/components/SelectedServiceCard/SelectedServiceCard";

const EmbeddingModelServerCard = ({
  data: { status, displayName },
}: ControlPlaneCardProps) => (
  <SelectedServiceCard serviceStatus={status} serviceName={displayName} />
);

export default EmbeddingModelServerCard;
