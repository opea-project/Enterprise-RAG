// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ControlPlaneCardProps } from "@/components/admin-panel/control-plane/cards";
import SelectedServiceCard from "@/components/admin-panel/control-plane/SelectedServiceCard/SelectedServiceCard";

const EmbeddingCard = ({
  data: { status, displayName, details },
}: ControlPlaneCardProps) => (
  <SelectedServiceCard
    serviceStatus={status}
    serviceName={displayName}
    serviceDetails={details}
  />
);

export default EmbeddingCard;
