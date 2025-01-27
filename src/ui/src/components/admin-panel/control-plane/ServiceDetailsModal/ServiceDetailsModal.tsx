// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsModal.scss";

import {
  ChangeArgumentsRequestData,
  GuardrailParams,
} from "@/api/models/systemFingerprint";
import GuardServiceDetailsModalContent from "@/components/admin-panel/control-plane/GuardServiceDetailsModalContent/GuardServiceDetailsModalContent";
import ServiceDetailsModalContent from "@/components/admin-panel/control-plane/ServiceDetailsModalContent/ServiceDetailsModalContent";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphSelectedServiceNodeSelector,
  setCanBeRendered,
  setChatQnAGraphEdges,
  setChatQnAGraphEditMode,
  setChatQnAGraphLoading,
  setChatQnAGraphNodes,
  setChatQnAGraphSelectedServiceNode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { addNotification } from "@/store/notifications.slice";

const ServiceDetailsModal = () => {
  const selectedServiceNode = useAppSelector(
    chatQnAGraphSelectedServiceNodeSelector,
  );
  const dispatch = useAppDispatch();

  const updateServiceArguments = async (
    name: string,
    data: GuardrailParams | ChangeArgumentsRequestData,
  ) => {
    dispatch(setChatQnAGraphLoading(true));

    const fetchGraphData = async () => {
      dispatch(setChatQnAGraphEditMode(false));
      dispatch(setChatQnAGraphSelectedServiceNode([]));
      dispatch(setChatQnAGraphLoading(true));

      try {
        const [fetchedDetails, parameters] = await Promise.all([
          SystemFingerprintService.getChatQnAServiceDetails(),
          SystemFingerprintService.appendArguments(),
        ]);

        if (fetchedDetails && parameters) {
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

    try {
      const changeArgumentsRequestBody = [{ name, data }];
      await SystemFingerprintService.changeArguments(
        changeArgumentsRequestBody,
      );
      fetchGraphData();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to change arguments";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  };

  const getContent = () => {
    if (selectedServiceNode) {
      const { id, data } = selectedServiceNode;
      const isInputGuard = ["input_guard", "output_guard"].includes(id);
      return isInputGuard ? (
        <GuardServiceDetailsModalContent
          serviceData={data}
          updateServiceArguments={updateServiceArguments}
        />
      ) : (
        <ServiceDetailsModalContent
          serviceData={data}
          updateServiceArguments={updateServiceArguments}
        />
      );
    } else {
      return (
        <div className="service-details-select-node-message">
          <p>Select service from the graph to see its details</p>
        </div>
      );
    }
  };

  return <div className="service-details-card">{getContent()}</div>;
};

export default ServiceDetailsModal;
