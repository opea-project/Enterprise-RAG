// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./GuardServiceDetailsModalContent.scss";

import { Fragment, useCallback, useEffect, useState } from "react";

import {
  ChangeArgumentsRequestData,
  GuardrailParams,
  ScannerArguments,
} from "@/api/models/systemFingerprint";
import ServiceArgumentValue from "@/components/admin-panel/control-plane/ServiceArgumentValue/ServiceArgumentValue";
import ServiceDetailsGrid from "@/components/admin-panel/control-plane/ServiceDetailsGrid/ServiceDetailsGrid";
import ServiceStatusIndicator from "@/components/admin-panel/control-plane/ServiceStatusIndicator/ServiceStatusIndicator";
import ServiceArgument, {
  ServiceArgumentInputValue,
} from "@/models/admin-panel/control-plane/serviceArgument";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import {
  chatQnAGraphEditModeEnabledSelector,
  setChatQnAGraphEditMode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

interface GuardServiceArgumentsGridData {
  [scannerName: string]: {
    [argumentName: string]: ServiceArgument;
  };
}

const getScannersArgsValuesObj = (dataObj: GuardServiceArgumentsGridData) =>
  Object.fromEntries(
    Object.entries(dataObj).map(([scannerName, scannerArgs]) => {
      const scannerArgsValues: ScannerArguments = {};
      for (const argName in scannerArgs) {
        scannerArgsValues[argName] = scannerArgs[argName].value;
      }
      return [scannerName, scannerArgsValues];
    }),
  );

const formatScannerName = (scannerName: string) =>
  scannerName
    .split("_")
    .map((v) => v.slice(0, 1).toUpperCase() + v.slice(1))
    .join(" ");

interface GuardServiceArgumentsGridValues {
  name: string;
  data: GuardServiceArgumentsGridData;
}

interface GuardServiceDetailsModalContentProps {
  serviceData: ServiceData;
  updateServiceArguments: (
    name: string,
    data: ChangeArgumentsRequestData,
  ) => void;
}

const GuardServiceDetailsModalContent = ({
  serviceData,
  updateServiceArguments,
}: GuardServiceDetailsModalContentProps) => {
  const dispatch = useAppDispatch();

  const editModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  const [serviceArgumentsGrid, setServiceArgumentsGrid] =
    useState<GuardServiceArgumentsGridValues>({ name: "", data: {} });
  const [initialServiceArgumentsGrid, setInitialServiceArgumentsGrid] =
    useState<GuardServiceArgumentsGridValues>({ name: "", data: {} });
  const [invalidArguments, setInvalidArguments] = useState<
    [string, string[]][]
  >([]);

  useEffect(() => {
    const gridData: GuardServiceArgumentsGridData = {};

    const guardArguments = serviceData.guardArgs
      ? Object.entries(serviceData.guardArgs)
      : [];

    for (const [scannerName, scannerArgs] of guardArguments) {
      gridData[scannerName] = {};
      for (const scannerArg of scannerArgs) {
        const { displayName } = scannerArg;
        gridData[scannerName][displayName] = scannerArg;
      }
    }

    const initialServiceArgumentsGrid = {
      name: serviceData.id,
      data: gridData,
    };
    setServiceArgumentsGrid(initialServiceArgumentsGrid);
    setInitialServiceArgumentsGrid(initialServiceArgumentsGrid);
  }, [serviceData.guardArgs, serviceData.id]);

  const handleArgumentValueChange = (
    argumentName: string,
    argumentValue: ServiceArgumentInputValue,
    scannerName: string,
  ) => {
    setServiceArgumentsGrid((prevArguments) => ({
      ...prevArguments,
      data: {
        ...prevArguments.data,
        [scannerName]: {
          ...prevArguments.data[scannerName],
          [argumentName]: {
            ...prevArguments.data[scannerName][argumentName],
            value: argumentValue,
          },
        },
      },
    }));
  };

  const handleArgumentValidityChange = useCallback(
    (argumentName: string, isArgumentInvalid: boolean, scannerName: string) => {
      const invalidScannerIndex = invalidArguments.findIndex(
        ([invalidScannerName]) => invalidScannerName === scannerName,
      );
      if (isArgumentInvalid) {
        if (invalidScannerIndex === -1) {
          setInvalidArguments((prevState) => [
            ...prevState,
            [scannerName, [argumentName]],
          ]);
        } else {
          setInvalidArguments((prevState) =>
            prevState.map(([invalidScannerName, invalidScannerArgs], index) =>
              index === invalidScannerIndex
                ? [
                    invalidScannerName,
                    Array.from(new Set([...invalidScannerArgs, argumentName])),
                  ]
                : [invalidScannerName, invalidScannerArgs],
            ),
          );
        }
      } else {
        if (invalidScannerIndex !== -1) {
          setInvalidArguments((prevState) =>
            prevState.map(([invalidScannerName, invalidScannerArgs], index) =>
              index === invalidScannerIndex
                ? [
                    invalidScannerName,
                    invalidScannerArgs.filter((name) => name !== argumentName),
                  ]
                : [invalidScannerName, invalidScannerArgs],
            ),
          );
        }
      }
    },
    [invalidArguments],
  );

  const handleEditArgumentsBtnClick = () => {
    dispatch(setChatQnAGraphEditMode(true));
  };

  const handleConfirmChangesBtnClick = () => {
    const guardServiceName = serviceArgumentsGrid.name;
    const guardServiceData: GuardrailParams = {};

    for (const guardScanner in serviceArgumentsGrid.data) {
      const scannerArguments = serviceArgumentsGrid.data[guardScanner];
      guardServiceData[guardScanner] = {};
      for (const scannerArgName in scannerArguments) {
        const scannerArgument = scannerArguments[scannerArgName];
        let scannerArgValue = scannerArgument.value;
        if (
          scannerArguments[scannerArgName]?.commaSeparated &&
          typeof scannerArgValue === "string"
        ) {
          scannerArgValue = scannerArgValue
            .split(",")
            .map((value) => value.trim());
        }
        guardServiceData[guardScanner][scannerArgName] = scannerArgValue;
      }
    }

    updateServiceArguments(guardServiceName, guardServiceData);
  };

  const handleCancelChangesBtnClick = () => {
    setServiceArgumentsGrid(initialServiceArgumentsGrid);
    dispatch(setChatQnAGraphEditMode(false));
  };

  const checkChanges = useCallback(() => {
    if (editModeEnabled) {
      const changes = [];
      const initialArgumentsValues = getScannersArgsValuesObj(
        initialServiceArgumentsGrid.data,
      );
      const currentArgumentsValues = getScannersArgsValuesObj(
        serviceArgumentsGrid.data,
      );

      for (const scannerName in initialArgumentsValues) {
        const initialScannerArgs = initialArgumentsValues[scannerName];
        for (const argName in initialScannerArgs) {
          const initialArgValue = initialArgumentsValues[scannerName][argName];
          const currentArgValue = currentArgumentsValues[scannerName][argName];

          if (initialArgValue !== currentArgValue) {
            changes.push(`${scannerName}.${argName}`);
          }
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
    invalidArguments.filter(
      (invalidScannerArgs) => invalidScannerArgs[1].length > 0,
    ).length > 0 || checkChanges();

  const getBottomPanel = () => {
    const bottomPanel = null;
    const serviceHasGuardArgs =
      serviceData?.guardArgs &&
      Object.entries(serviceData.guardArgs).length !== 0;
    if (serviceHasGuardArgs) {
      return editModeEnabled ? (
        <div className="guard-details-bottom-panel">
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
        </div>
      ) : (
        <div className="guard-details-bottom-panel">
          <button
            className="button--small w-full"
            onClick={handleEditArgumentsBtnClick}
          >
            Edit Service Arguments
          </button>
        </div>
      );
    }
    return bottomPanel;
  };

  return (
    <div className="guard-details-content-panel">
      <div>
        <header className="guard-details-card-header">
          <ServiceStatusIndicator status={serviceData.status} />
          <p className="guard-details__guard-name">{serviceData.displayName}</p>
        </header>
        <div className="guard-details-content">
          {serviceData?.details &&
            Object.entries(serviceData.details).length !== 0 && (
              <ServiceDetailsGrid details={serviceData.details} />
            )}
          {serviceData?.guardArgs &&
            Object.entries(serviceData.guardArgs).length !== 0 && (
              <>
                <p className="guard-arguments-grid-header">
                  Scanners Arguments
                </p>
                {Object.entries(serviceData.guardArgs).map(
                  ([scannerName, scannerArgs]) => (
                    <Fragment key={scannerName}>
                      <p className="guard-scanner-name">
                        {formatScannerName(scannerName)}
                      </p>
                      <div className="guard-arguments-grid">
                        {scannerArgs.map((argumentData) => (
                          <Fragment
                            key={`${scannerName}.${argumentData.displayName}`}
                          >
                            <p className="guard-argument-label">
                              {argumentData.displayName}
                            </p>
                            <ServiceArgumentValue
                              argumentData={argumentData}
                              onArgumentValueChange={(
                                argumentName: string,
                                argumentValue: ServiceArgumentInputValue,
                              ) =>
                                handleArgumentValueChange(
                                  argumentName,
                                  argumentValue,
                                  scannerName,
                                )
                              }
                              onArgumentValidityChange={(
                                argumentName: string,
                                isArgumentInvalid: boolean,
                              ) =>
                                handleArgumentValidityChange(
                                  argumentName,
                                  isArgumentInvalid,
                                  scannerName,
                                )
                              }
                            />
                          </Fragment>
                        ))}
                      </div>
                    </Fragment>
                  ),
                )}
              </>
            )}
        </div>
      </div>
      {getBottomPanel()}
    </div>
  );
};

export default GuardServiceDetailsModalContent;
