// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsModal.scss";

import {
  ChangeArgumentsRequestData,
  GuardrailParams,
  ServicesParameters,
} from "@/api/models/systemFingerprint";
import GuardServiceDetailsModalContent from "@/components/admin-panel/control-plane/GuardServiceDetailsModalContent/GuardServiceDetailsModalContent";
import ServiceDetailsModalContent from "@/components/admin-panel/control-plane/ServiceDetailsModalContent/ServiceDetailsModalContent";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphSelectedServiceNodeSelector,
  setChatQnAGraphEdges,
  setChatQnAGraphEditMode,
  setChatQnAGraphLoading,
  setChatQnAGraphNodes,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ServiceDetailsModal = () => {
  const selectedServiceNode = useAppSelector(
    chatQnAGraphSelectedServiceNodeSelector,
  );
  const dispatch = useAppDispatch();

  const updateServiceArguments = (
    name: string,
    data: GuardrailParams | ChangeArgumentsRequestData,
  ) => {
    const changeArgumentsRequestBody = [{ name, data }];

    dispatch(setChatQnAGraphLoading(true));
    SystemFingerprintService.changeArguments(changeArgumentsRequestBody).then(
      () => {
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
      },
    );

    dispatch(setChatQnAGraphEditMode(false));
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
