// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceStatusIndicator.scss";

import classNames from "classnames";

import Tooltip from "@/components/ui/Tooltip/Tooltip";
import { ServiceStatus } from "@/features/admin-panel/control-plane/types";

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
    "service-status-indicator--ready": status === ServiceStatus.Ready,
    "service-status-indicator--not-ready": status === ServiceStatus.NotReady,
    "service-status-indicator--not-available":
      status === ServiceStatus.NotAvailable,
    "service-status-indicator__node": forNode,
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
