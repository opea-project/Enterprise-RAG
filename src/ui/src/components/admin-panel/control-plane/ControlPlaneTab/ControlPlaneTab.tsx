// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlaneTab.scss";

import { useEffect } from "react";
import { BsHurricane } from "react-icons/bs";

import ChatQnAGraph from "@/components/admin-panel/control-plane/ChatQnAGraph/ChatQnAGraph";
import ServiceDetailsModal from "@/components/admin-panel/control-plane/ServiceDetailsModal/ServiceDetailsModal";
import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceData";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphCanBeRenderedSelector,
  chatQnAGraphLoadingSelector,
  setCanBeRendered,
  setChatQnAGraphEdges,
  setChatQnAGraphLoading,
  setChatQnAGraphNodes,
  setChatQnAGraphSelectedServiceNode,
  setHasInputGuard,
  setHasOutputGuard,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { addNotification } from "@/store/notifications.slice";

const ServiceStatusLegend = () => (
  <div className="chatqna-graph-legend">
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.Ready} />
      <p>Ready</p>
    </div>
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.NotReady} />
      <p>Not Ready</p>
    </div>
    <div className="chatqna-graph-legend-item">
      <ServiceStatusIndicator status={ServiceStatus.NotAvailable} />
      <p>Status Not Available</p>
    </div>
  </div>
);

const ControlPlaneTab = () => {
  const dispatch = useAppDispatch();
  const loading = useAppSelector(chatQnAGraphLoadingSelector);
  const canBeRendered = useAppSelector(chatQnAGraphCanBeRenderedSelector);

  useEffect(() => {
    dispatch(setChatQnAGraphSelectedServiceNode([]));
  }, [dispatch]);

  useEffect(() => {
    const fetchGraphData = async () => {
      dispatch(setChatQnAGraphLoading(true));

      try {
        const [fetchedDetails, parameters] = await Promise.all([
          SystemFingerprintService.getChatQnAServiceDetails(),
          SystemFingerprintService.appendArguments(),
        ]);

        if (fetchedDetails && parameters) {
          const hasInputGuard = fetchedDetails.input_guard.status !== undefined;
          const hasOutputGuard =
            fetchedDetails.output_guard.status !== undefined;
          dispatch(setHasInputGuard(hasInputGuard));
          dispatch(setHasOutputGuard(hasOutputGuard));

          dispatch(
            setChatQnAGraphNodes({
              parameters,
              fetchedDetails: fetchedDetails ?? {},
            }),
          );
          dispatch(setChatQnAGraphEdges());
          dispatch(setCanBeRendered(true));
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error occurred";
        dispatch(addNotification({ severity: "error", text: errorMessage }));
        dispatch(setCanBeRendered(false));
      } finally {
        dispatch(setChatQnAGraphLoading(false));
      }
    };

    fetchGraphData();
  }, [dispatch]);

  const getControlPlaneContent = () => {
    if (loading) {
      return (
        <div className="configure-services-panel-loading__overlay">
          <div className="configure-services-panel-loading__message">
            <BsHurricane className="animate-spin" />
            <p>Loading...</p>
          </div>
        </div>
      );
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
      <ServiceDetailsModal />
    </div>
  );
};

export default ControlPlaneTab;
