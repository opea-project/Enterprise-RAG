// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlanePanel.scss";

import { LoadingFallback } from "@intel-enterprise-rag-ui/components";
import { ConfigurableServiceIcon } from "@intel-enterprise-rag-ui/icons";
import { ComponentType } from "react";

import { ServiceStatusIndicator } from "@/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceStatus } from "@/types";

const ServiceStatusLegend = () => (
  <div className="graph-legend">
    <div className="graph-legend__item">
      <ServiceStatusIndicator status={ServiceStatus.Ready} noTooltip />
      <p>Ready</p>
    </div>
    <div className="graph-legend__item">
      <ServiceStatusIndicator status={ServiceStatus.NotReady} noTooltip />
      <p>Not Ready</p>
    </div>
    <div className="graph-legend__item">
      <ServiceStatusIndicator status={ServiceStatus.NotAvailable} noTooltip />
      <p>Status Not Available</p>
    </div>
    <div className="graph-legend__item">
      <ConfigurableServiceIcon />
      <p>Configurable Service</p>
    </div>
  </div>
);

interface ControlPlanePanelProps {
  isLoading: boolean;
  isRenderable: boolean;
  Graph: ComponentType;
}

export const ControlPlanePanel = ({
  isLoading,
  isRenderable,
  Graph,
}: ControlPlanePanelProps) => {
  const getControlPlaneContent = () => {
    if (isLoading) {
      return <LoadingFallback />;
    } else {
      if (isRenderable) {
        return (
          <>
            <ServiceStatusLegend />
            <Graph />
          </>
        );
      } else {
        return (
          <div className="control-plane-panel__not-renderable">
            <p>Pipeline graph cannot be rendered</p>
          </div>
        );
      }
    }
  };

  return (
    <div className="control-plane-panel">
      <div className="graph-wrapper">{getControlPlaneContent()}</div>
    </div>
  );
};
