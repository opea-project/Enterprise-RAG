// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlaneTab.scss";

import { useEffect } from "react";

import LoadingFallback from "@/components/ui/LoadingFallback/LoadingFallback";
import ChatQnAGraph from "@/features/admin-panel/control-plane/components/ChatQnAGraph/ChatQnAGraph";
import ServiceCard from "@/features/admin-panel/control-plane/components/ServiceCard/ServiceCard";
import ServiceStatusIndicator from "@/features/admin-panel/control-plane/components/ServiceStatusIndicator/ServiceStatusIndicator";
import {
  chatQnAGraphCanBeRenderedSelector,
  chatQnAGraphLoadingSelector,
  fetchGraphData,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceStatus } from "@/features/admin-panel/control-plane/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

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
  </div>
);

const ControlPlaneTab = () => {
  const dispatch = useAppDispatch();
  const loading = useAppSelector(chatQnAGraphLoadingSelector);
  const canBeRendered = useAppSelector(chatQnAGraphCanBeRenderedSelector);

  useEffect(() => {
    dispatch(fetchGraphData());
  }, [dispatch]);

  const getControlPlaneContent = () => {
    if (loading) {
      return <LoadingFallback />;
    } else {
      if (canBeRendered) {
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
    <div className="configure-services-panel">
      <div className="chatqna-graph-wrapper">{getControlPlaneContent()}</div>
      <ServiceCard />
    </div>
  );
};

export default ControlPlaneTab;
