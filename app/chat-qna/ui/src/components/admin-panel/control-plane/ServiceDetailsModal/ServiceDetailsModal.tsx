// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsModal.scss";

import ServiceDetailsModalContent from "@/components/admin-panel/control-plane/ServiceDetailsModalContent/ServiceDetailsModalContent";
import { chatQnAGraphSelectedServiceNodeSelector } from "@/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

const ServiceDetailsModal = () => {
  const selectedServiceNode = useAppSelector(
    chatQnAGraphSelectedServiceNodeSelector,
  );

  return (
    <div className="service-details-card">
      {selectedServiceNode ? (
        <ServiceDetailsModalContent serviceData={selectedServiceNode.data} />
      ) : (
        <div className="service-details-select-node-message">
          <p>Select service from the graph to see its details</p>
        </div>
      )}
    </div>
  );
};

export default ServiceDetailsModal;
