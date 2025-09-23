// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceCard.scss";

import {
  cards,
  SelectedServiceId,
} from "@/features/admin-panel/control-plane/components/cards";
import { chatQnAGraphSelectedServiceNodeSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

const ServiceCard = () => {
  const selectedServiceNode = useAppSelector(
    chatQnAGraphSelectedServiceNodeSelector,
  );

  if (selectedServiceNode === null) {
    return <NoServiceSelectedCard />;
  }

  const { id, data } = selectedServiceNode;
  const selectedServiceId = id as SelectedServiceId;
  const SelectedServiceCard = cards[selectedServiceId];
  return <SelectedServiceCard data={data} />;
};

const NoServiceSelectedCard = () => (
  <div className="no-service-selected-card">
    <p>Select service from the graph to see its details</p>
  </div>
);

export default ServiceCard;
