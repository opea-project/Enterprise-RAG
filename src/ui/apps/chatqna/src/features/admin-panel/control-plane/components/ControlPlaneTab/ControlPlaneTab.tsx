// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlaneTab.scss";

import { LoadingFallback } from "@intel-enterprise-rag-ui/components";
import { ConfigurableServiceIcon } from "@intel-enterprise-rag-ui/icons";

import { useGetServicesDataQuery } from "@/features/admin-panel/control-plane/api";
import ChatQnAGraph from "@/features/admin-panel/control-plane/components/ChatQnAGraph/ChatQnAGraph";
import ServiceCard from "@/features/admin-panel/control-plane/components/ServiceCard/ServiceCard";
import ServiceStatusIndicator from "@/features/admin-panel/control-plane/components/ServiceStatusIndicator/ServiceStatusIndicator";
import {
  chatQnAGraphIsLoadingSelector,
  chatQnAGraphIsRenderableSelector,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceStatus } from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

const ServiceStatusLegend = () => (
  <div className="chatqna-graph-legend">
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.Ready} noTooltip />
      <p>Ready</p>
    </div>
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.NotReady} noTooltip />
      <p>Not Ready</p>
    </div>
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.NotAvailable} noTooltip />
      <p>Status Not Available</p>
    </div>
    <div className="chatqna-graph-legend-item mt-3">
      <ConfigurableServiceIcon className="text-xs" />
      <p>Configurable Service</p>
    </div>
  </div>
);

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const isLoading = useAppSelector(chatQnAGraphIsLoadingSelector);
  const isRenderable = useAppSelector(chatQnAGraphIsRenderableSelector);

  const getControlPlaneContent = () => {
    if (isLoading) {
      return <LoadingFallback />;
    } else {
      if (isRenderable) {
        return (
          <>
            <ServiceStatusLegend />
            <ChatQnAGraph />
          </>
        );
      } else {
        return (
          <div className="flex h-full w-full items-center justify-center">
            <p>Pipeline graph cannot be rendered</p>
          </div>
        );
      }
    }
  };

  return (
    <div className="control-plane-panel">
      <div className="chatqna-graph-wrapper">{getControlPlaneContent()}</div>
      <ServiceCard />
    </div>
  );
};

export default ControlPlaneTab;
