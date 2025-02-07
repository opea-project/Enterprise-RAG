// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceStatusIndicator.scss";

import classNames from "classnames";

import Tooltip from "@/components/shared/Tooltip/Tooltip";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceData";

interface ServiceStatusIndicatorProps {
  status?: ServiceStatus;
  forNode?: boolean;
  noTooltip?: boolean;
}

const ServiceStatusIndicator = ({
  status = ServiceStatus.NotAvailable,
  forNode,
  noTooltip,
}: ServiceStatusIndicatorProps) => {
  const serviceStatusIndicatorClassNames = classNames({
    "service-status-indicator": true,
    [status.split(" ").join("-").toLowerCase()]: true,
    "service-status-indicator--node": forNode,
  });

  if (noTooltip) {
    return <div className={serviceStatusIndicatorClassNames}></div>;
  }

  return (
    <Tooltip text={status} position={forNode ? "top" : "left"}>
      <div className={serviceStatusIndicatorClassNames}></div>
    </Tooltip>
  );
};

export default ServiceStatusIndicator;
