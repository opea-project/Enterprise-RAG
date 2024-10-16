// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "@xyflow/react/dist/style.css";
import "./ControlPlaneTab.scss";

import { useEffect } from "react";
import { BsHurricane } from "react-icons/bs";

import { ServicesParameters } from "@/api/models/system-fingerprint/appendArguments";
import ChatQnAGraph from "@/components/admin-panel/control-plane/ChatQnAGraph/ChatQnAGraph";
import ServiceDetailsModal from "@/components/admin-panel/control-plane/ServiceDetailsModal/ServiceDetailsModal";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphLoadingSelector,
  setChatQnAGraphEdges,
  setChatQnAGraphInitialNodes,
  setChatQnAGraphLoading,
  setChatQnAGraphSelectedServiceNode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { graphEdges } from "@/utils/chatQnAGraph";

const ControlPlaneTab = () => {
  const dispatch = useAppDispatch();
  const loading = useAppSelector(chatQnAGraphLoadingSelector);

  useEffect(() => {
    dispatch(setChatQnAGraphSelectedServiceNode([]));
  }, []);

  useEffect(() => {
    dispatch(setChatQnAGraphLoading(true));

    SystemFingerprintService.appendArguments().then(
      (parameters: ServicesParameters) => {
        dispatch(setChatQnAGraphInitialNodes(parameters));
        dispatch(setChatQnAGraphEdges(graphEdges));
        dispatch(setChatQnAGraphLoading(false));
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
          <ChatQnAGraph />
        )}
      </div>
      <ServiceDetailsModal />
    </div>
  );
};

export default ControlPlaneTab;
