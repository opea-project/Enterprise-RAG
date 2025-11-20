// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceStatusIndicator.scss";

import { Tooltip } from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";

import { ServiceStatus } from "@/types";

interface ServiceStatusIndicatorProps {
  status?: ServiceStatus;
  forNode?: boolean;
  noTooltip?: boolean;
}

export const ServiceStatusIndicator = ({
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
    <Tooltip
      title={status}
      trigger={<div className={serviceStatusIndicatorClassNames}></div>}
      placement={forNode ? "top" : "left"}
    />
  );
};
