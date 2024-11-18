// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceNode.scss";

import { Handle } from "@xyflow/react";
import classNames from "classnames";
import { memo } from "react";

import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";

interface ServiceNodeProps {
  data: ServiceData;
}

const ServiceNode = ({
  data: {
    displayName,
    targetPosition,
    sourcePosition,
    additionalTargetPosition,
    additionalTargetId,
    additionalSourcePosition,
    additionalSourceId,
    selected,
    status,
  },
}: ServiceNodeProps) => {
  const serviceNodeClassNames = classNames({
    "service-node": true,
    "service-node-selected": selected,
  });

  return (
    <>
      {targetPosition && (
        <Handle
          type="target"
          position={targetPosition}
          className="service-node-handle"
        />
      )}
      <div className={serviceNodeClassNames}>
        <ServiceStatusIndicator status={status} forNode />
        <p>{displayName}</p>
      </div>
      {sourcePosition && (
        <Handle
          type="source"
          position={sourcePosition}
          className="service-node-handle"
        />
      )}
      {additionalTargetPosition && additionalTargetId && (
        <Handle
          id={additionalTargetId}
          type="target"
          position={additionalTargetPosition}
          className="service-node-handle"
        />
      )}
      {additionalSourcePosition && additionalSourceId && (
        <Handle
          id={additionalSourceId}
          type="source"
          position={additionalSourcePosition}
          className="service-node-handle"
        />
      )}
    </>
  );
};

export default memo(ServiceNode);
