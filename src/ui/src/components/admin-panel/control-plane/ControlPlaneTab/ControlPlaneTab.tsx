// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlaneTab.scss";

import { useEffect } from "react";
import { BsHurricane } from "react-icons/bs";

import { ServicesParameters } from "@/api/models/systemFingerprint";
import ChatQnAGraph from "@/components/admin-panel/control-plane/ChatQnAGraph/ChatQnAGraph";
import ServiceDetailsModal from "@/components/admin-panel/control-plane/ServiceDetailsModal/ServiceDetailsModal";
import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceStatus } from "@/models/admin-panel/control-plane/serviceData";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphLoadingSelector,
  setChatQnAGraphEdges,
  setChatQnAGraphLoading,
  setChatQnAGraphNodes,
  setChatQnAGraphSelectedServiceNode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

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

  useEffect(() => {
    dispatch(setChatQnAGraphSelectedServiceNode([]));
  }, [dispatch]);

  useEffect(() => {
    dispatch(setChatQnAGraphLoading(true));

    SystemFingerprintService.getChatQnAServiceDetails().then(
      (fetchedDetails) => {
        SystemFingerprintService.appendArguments().then(
          (parameters: ServicesParameters) => {
            dispatch(
              setChatQnAGraphNodes({
                parameters,
                fetchedDetails: fetchedDetails ?? {},
              }),
            );
            dispatch(setChatQnAGraphEdges());
            dispatch(setChatQnAGraphLoading(false));
          },
        );
      },
    );
  }, [dispatch]);

  return (
    <div className="configure-services-panel">
      <div className="chatqna-graph-wrapper">
        {loading ? (
          <div className="configure-services-panel-loading__overlay">
            <div className="configure-services-panel-loading__message">
              <BsHurricane className="animate-spin" />
              <p>Loading...</p>
            </div>
          </div>
        ) : (
          <>
            <ServiceStatusLegend />
            <ChatQnAGraph />
          </>
        )}
      </div>
      <ServiceDetailsModal />
    </div>
  );
};

export default ControlPlaneTab;
