// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsModalContent.scss";

import { useCallback, useEffect, useState } from "react";

import { ServicesParameters } from "@/api/models/system-fingerprint/appendArguments";
import ServiceArgumentsGrid from "@/components/admin-panel/control-plane/ServiceArgumentsGrid/ServiceArgumentsGrid";
import ServiceDetailsGrid from "@/components/admin-panel/control-plane/ServiceDetailsGrid/ServiceDetailsGrid";
import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  chatQnAGraphEditModeEnabledSelector,
  setChatQnAGraphEdges,
  setChatQnAGraphEditMode,
  setChatQnAGraphInitialNodes,
  setChatQnAGraphLoading,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { graphEdges } from "@/utils/chatQnAGraph";

export interface ServiceArgumentsGridValues {
  name: string;
  data: {
    [argumentName: string]: ServiceArgument;
  };
}

interface ServiceDetailsModalContentProps {
  serviceData: ServiceData;
}

const ServiceDetailsModalContent = ({
  serviceData,
}: ServiceDetailsModalContentProps) => {
  const dispatch = useAppDispatch();

  const editModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  const [serviceArgumentsGrid, setServiceArgumentsGrid] =
    useState<ServiceArgumentsGridValues>({ name: "", data: {} });
  const [initialServiceArgumentsGrid, setInitialServiceArgumentsGrid] =
    useState<ServiceArgumentsGridValues>({ name: "", data: {} });
  const [invalidArguments, setInvalidArguments] = useState<string[]>([]);

  useEffect(() => {
    const serviceArguments = serviceData.args ?? [];
    const gridData: { [key: string]: ServiceArgument } = {};
    for (const argument of serviceArguments) {
      const { displayName } = argument;
      gridData[displayName] = argument;
    }

    const initialServiceArgumentsGrid = {
      name: serviceData.id,
      data: gridData,
    };
    setServiceArgumentsGrid(initialServiceArgumentsGrid);
    setInitialServiceArgumentsGrid(initialServiceArgumentsGrid);
  }, [serviceData.args, serviceData.id]);

  const handleArgumentValueChange = (
    argumentName: string,
    argumentValue: string | number | boolean | null,
  ) => {
    setServiceArgumentsGrid((prevArguments) => ({
      ...prevArguments,
      data: {
        ...prevArguments.data,
        [argumentName]: {
          ...prevArguments.data[argumentName],
          value: argumentValue,
        },
      },
    }));
  };

  const handleArgumentValidityChange = useCallback(
    (argumentName: string, isArgumentInvalid: boolean) => {
      if (!isArgumentInvalid && invalidArguments.includes(argumentName)) {
        setInvalidArguments((prevState) =>
          prevState.filter((name) => name !== argumentName),
        );
      } else if (
        isArgumentInvalid &&
        !invalidArguments.includes(argumentName)
      ) {
        setInvalidArguments((prevState) => [...prevState, argumentName]);
      }
    },
    [invalidArguments],
  );

  const handleEditArgumentsBtnClick = () => {
    dispatch(setChatQnAGraphEditMode(true));
  };

  const handleConfirmChangesBtnClick = () => {
    const argumentsDataEntries = Object.entries(serviceArgumentsGrid.data).map(
      ([name, { value }]) => [name, value],
    );
    const data = Object.fromEntries(argumentsDataEntries);
    const changeArgumentsRequestBody = [
      {
        name: serviceArgumentsGrid.name,
        data,
      },
    ];

    dispatch(setChatQnAGraphLoading(true));
    SystemFingerprintService.changeArguments(changeArgumentsRequestBody).then(
      () => {
        SystemFingerprintService.appendArguments().then(
          (parameters: ServicesParameters) => {
            dispatch(setChatQnAGraphInitialNodes(parameters));
            dispatch(setChatQnAGraphEdges(graphEdges));
            dispatch(setChatQnAGraphLoading(false));
          },
        );
      },
    );

    dispatch(setChatQnAGraphEditMode(false));
  };

  const handleCancelChangesBtnClick = () => {
    setServiceArgumentsGrid(initialServiceArgumentsGrid);
    dispatch(setChatQnAGraphEditMode(false));
  };

  const checkChanges = useCallback(() => {
    if (editModeEnabled) {
      const changes = [];
      const initialArgumentsValues = Object.fromEntries(
        Object.entries(initialServiceArgumentsGrid.data).map(
          ([name, argumentData]) => [name, argumentData.value],
        ),
      );
      const currentArgumentsValues = Object.fromEntries(
        Object.entries(serviceArgumentsGrid.data).map(
          ([name, argumentData]) => [name, argumentData.value],
        ),
      );
      for (const argumentName in initialArgumentsValues) {
        const initialValue = initialArgumentsValues[argumentName];
        const currentValue = currentArgumentsValues[argumentName];
        if (initialValue !== currentValue) {
          changes.push(argumentName);
        }
      }

      return changes.length === 0;
    } else {
      return true;
    }
  }, [
    editModeEnabled,
    initialServiceArgumentsGrid.data,
    serviceArgumentsGrid.data,
  ]);

  const confirmChangesBtnDisabled =
    invalidArguments.length > 0 || checkChanges();

  return (
    <div className="service-details-content-panel">
      <div className="p-4">
        <header className="service-details-card-header">
          <ServiceStatusIndicator status={serviceData.status} />
          <p className="service-details__service-name">
            {serviceData.displayName}
          </p>
        </header>
        <div className="service-details-content">
          {serviceData?.details &&
            Object.entries(serviceData.details).length !== 0 && (
              <ServiceDetailsGrid details={serviceData.details} />
            )}
          {serviceData?.args && serviceData.args.length !== 0 && (
            <ServiceArgumentsGrid
              argumentsGridValues={serviceArgumentsGrid}
              onArgumentValueChange={handleArgumentValueChange}
              onArgumentValidityChange={handleArgumentValidityChange}
            />
          )}
        </div>
      </div>
      {serviceData?.args && serviceData.args.length !== 0 && (
        <div className="service-details-bottom-panel">
          {editModeEnabled ? (
            <>
              <button
                className="button--small button__success w-full"
                disabled={confirmChangesBtnDisabled}
                onClick={handleConfirmChangesBtnClick}
              >
                Confirm Changes
              </button>
              <button
                className="button--small outlined-button--primary w-full"
                onClick={handleCancelChangesBtnClick}
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              className="button--small w-full"
              onClick={handleEditArgumentsBtnClick}
            >
              Edit Service Arguments
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ServiceDetailsModalContent;
