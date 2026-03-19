// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlanePanel.scss";

import {
  IconButton,
  LoadingFallback,
  Tooltip,
} from "@intel-enterprise-rag-ui/components";
import { ConfigurableServiceIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { ComponentType, useCallback, useState } from "react";

import { ServiceStatusIndicator } from "@/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceStatus } from "@/types";

const ServiceStatusLegend = () => (
  <div className="graph-legend" data-testid="graph-legend">
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
  ConfigPanel?: ComponentType;
  onConfigPanelToggle?: (isVisible: boolean) => void;
}

export const ControlPlanePanel = ({
  isLoading,
  isRenderable,
  Graph,
  ConfigPanel,
  onConfigPanelToggle,
}: ControlPlanePanelProps) => {
  const [isConfigPanelVisible, setIsConfigPanelVisible] = useState(true);

  const toggleConfigPanel = useCallback(() => {
    const newVisibility = !isConfigPanelVisible;
    setIsConfigPanelVisible(newVisibility);
    onConfigPanelToggle?.(newVisibility);

    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 350);
  }, [isConfigPanelVisible, onConfigPanelToggle]);

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

  const controlPlanePanelClassName = classNames("control-plane-panel", {
    "control-plane-panel__with-config-panel":
      !!ConfigPanel && isConfigPanelVisible,
  });

  const configPanelWrapperClassName = classNames("config-panel-wrapper", {
    "config-panel-wrapper--visible": isConfigPanelVisible,
    "config-panel-wrapper--hidden": !isConfigPanelVisible,
  });

  const toggleWrapperClassName = classNames("config-panel-toggle-wrapper", {
    "config-panel-toggle-wrapper--panel-hidden": !isConfigPanelVisible,
  });

  const toggleButtonLabel = isConfigPanelVisible
    ? "Hide side panel"
    : "Show side panel";

  const toggleButtonIcon = isConfigPanelVisible ? "panel-hide" : "panel-show";

  return (
    <div
      className={controlPlanePanelClassName}
      data-testid="control-plane-panel"
    >
      <div className="graph-wrapper">{getControlPlaneContent()}</div>
      {ConfigPanel && (
        <>
          <div className={configPanelWrapperClassName}>
            <ConfigPanel />
          </div>
          <div className={toggleWrapperClassName}>
            <Tooltip
              title={toggleButtonLabel}
              placement="left"
              trigger={
                <IconButton
                  icon={toggleButtonIcon}
                  className="config-panel-toggle-button"
                  onPress={toggleConfigPanel}
                  aria-label={toggleButtonLabel}
                />
              }
            />
          </div>
        </>
      )}
    </div>
  );
};
