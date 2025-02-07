// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceDetailsModalContent.scss";

import { useCallback, useEffect, useState } from "react";

import { ChangeArgumentsRequestData } from "@/api/models/systemFingerprint";
import ServiceArgumentsGrid from "@/components/admin-panel/control-plane/ServiceArgumentsGrid/ServiceArgumentsGrid";
import ServiceDetailsGrid from "@/components/admin-panel/control-plane/ServiceDetailsGrid/ServiceDetailsGrid";
import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import Button from "@/components/shared/Button/Button";
import ServiceArgument, {
  ServiceArgumentInputValue,
} from "@/models/admin-panel/control-plane/serviceArgument";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import {
  chatQnAGraphEditModeEnabledSelector,
  setChatQnAGraphEditMode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

interface ServiceArgumentsGridData {
  [argumentName: string]: ServiceArgument;
}

export interface ServiceArgumentsGridValues {
  name: string;
  data: ServiceArgumentsGridData;
}

interface ServiceDetailsModalContentProps {
  serviceData: ServiceData;
  updateServiceArguments: (
    name: string,
    data: ChangeArgumentsRequestData,
  ) => void;
}

const ServiceDetailsModalContent = ({
  serviceData,
  updateServiceArguments,
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

    const gridData: ServiceArgumentsGridData = {};
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
    argumentValue: ServiceArgumentInputValue,
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
    const serviceName = serviceArgumentsGrid.name;
    const serviceData = Object.fromEntries(argumentsDataEntries);
    updateServiceArguments(serviceName, serviceData);
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

  let bottomPanel = null;
  if (serviceData?.args && serviceData.args.length !== 0) {
    if (editModeEnabled) {
      bottomPanel = (
        <div className="service-details-bottom-panel">
          <Button
            size="sm"
            color="success"
            fullWidth
            disabled={confirmChangesBtnDisabled}
            onClick={handleConfirmChangesBtnClick}
          >
            Confirm Changes
          </Button>
          <Button
            size="sm"
            variant="outlined"
            fullWidth
            onClick={handleCancelChangesBtnClick}
          >
            Cancel
          </Button>
        </div>
      );
    } else {
      bottomPanel = (
        <div className="service-details-bottom-panel">
          <Button size="sm" fullWidth onClick={handleEditArgumentsBtnClick}>
            Edit Service Arguments
          </Button>
        </div>
      );
    }
  }

  return (
    <div className="service-details-content-panel">
      <div>
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
      {bottomPanel}
    </div>
  );
};

export default ServiceDetailsModalContent;
