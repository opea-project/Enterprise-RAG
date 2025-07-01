// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceNode.scss";

import { Handle } from "@xyflow/react";
import classNames from "classnames";
import { memo } from "react";

import ConfigurableServiceIcon from "@/components/icons/ConfigurableServiceIcon/ConfigurableServiceIcon";
import ServiceStatusIndicator from "@/features/admin-panel/control-plane/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceData } from "@/features/admin-panel/control-plane/types";

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
    configurable,
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
        {configurable && (
          <ConfigurableServiceIcon className="service-node__icon" />
        )}
        <ServiceStatusIndicator status={status} forNode noTooltip />
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
