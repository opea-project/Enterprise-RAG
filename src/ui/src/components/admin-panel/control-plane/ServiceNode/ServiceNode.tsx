// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceNode.scss";

import { Handle } from "@xyflow/react";
import classNames from "classnames";
import { memo } from "react";

import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceData } from "@/types/admin-panel/control-plane";

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
    "service-node--selected": selected,
  });

  return (
    <>
      {targetPosition && (
        <Handle
          type="target"
          position={targetPosition}
          className="service-node__handle"
        />
      )}
      <div className={serviceNodeClassNames}>
        <ServiceStatusIndicator status={status} forNode />
        <div className="service-node__label">
          <p>{displayName}</p>
        </div>
      </div>
      {sourcePosition && (
        <Handle
          type="source"
          position={sourcePosition}
          className="service-node__handle"
        />
      )}
      {additionalTargetPosition && additionalTargetId && (
        <Handle
          id={additionalTargetId}
          type="target"
          position={additionalTargetPosition}
          className="service-node__handle"
        />
      )}
      {additionalSourcePosition && additionalSourceId && (
        <Handle
          id={additionalSourceId}
          type="source"
          position={additionalSourcePosition}
          className="service-node__handle"
        />
      )}
    </>
  );
};

export default memo(ServiceNode);
