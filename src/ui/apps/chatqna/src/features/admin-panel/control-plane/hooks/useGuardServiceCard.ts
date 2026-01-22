// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import { useChangeArgumentsMutation } from "@/features/admin-panel/control-plane/api";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
  ServiceArgumentInputValue,
} from "@/features/admin-panel/control-plane/types";
import { ChangeArgumentsRequestData } from "@/features/admin-panel/control-plane/types/api";

type ArgumentsForm = Record<string, Record<string, ServiceArgumentInputValue>>;

const useGuardServiceCard = <T>(guardName: string, args?: T) => {
  const [changeArguments] = useChangeArgumentsMutation();

  const [invalidArguments, setInvalidArguments] = useState<
    [string, string[]][]
  >([]);
  const [argumentsForm, setArgumentsForm] = useState<T>((args ?? {}) as T);
  const [previousArgumentsValues, setPreviousArgumentsValues] = useState<T>(
    (args ?? {}) as T,
  );
  const [isHydrated, setIsHydrated] = useState<boolean>(
    !!args && Object.keys(args as object).length > 0,
  );

  useEffect(() => {
    if (args !== undefined) {
      setArgumentsForm(args as T);
      setPreviousArgumentsValues(args as T);
      setIsHydrated(true);
    }
  }, [args]);

  const onArgumentValueChange =
    (scannerName: string): OnArgumentValueChangeHandler =>
    (argumentName, argumentValue) => {
      setArgumentsForm((prevArguments) => ({
        ...prevArguments,
        [scannerName]: {
          ...(prevArguments as ArgumentsForm)[scannerName],
          [argumentName]: argumentValue,
        },
      }));
    };

  const onArgumentValidityChange = useCallback(
    (scannerName: string): OnArgumentValidityChangeHandler =>
      (argumentName, isArgumentInvalid) => {
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
              prevState.map(
                ([invalidScannerName, invalidScannerArgs], index) =>
                  index === invalidScannerIndex
                    ? [
                        invalidScannerName,
                        Array.from(
                          new Set([...invalidScannerArgs, argumentName]),
                        ),
                      ]
                    : [invalidScannerName, invalidScannerArgs],
              ),
            );
          }
        } else {
          if (invalidScannerIndex !== -1) {
            setInvalidArguments((prevState) =>
              prevState.map(
                ([invalidScannerName, invalidScannerArgs], index) =>
                  index === invalidScannerIndex
                    ? [
                        invalidScannerName,
                        invalidScannerArgs.filter(
                          (name) => name !== argumentName,
                        ),
                      ]
                    : [invalidScannerName, invalidScannerArgs],
              ),
            );
          }
        }
      },
    [invalidArguments],
  );

  const onConfirmChangesButtonClick = () => {
    const changeArgumentsRequest = [
      {
        name: guardName,
        data: argumentsForm as ChangeArgumentsRequestData,
      },
    ];

    changeArguments(changeArgumentsRequest);
  };

  const onCancelChangesButtonClick = () => {
    setArgumentsForm(previousArgumentsValues);
    setInvalidArguments([]);
  };

  const isGuardFormModified = () =>
    Object.entries(previousArgumentsValues as object).some(
      ([scannerName, initialScannerArgs]) =>
        Object.entries(initialScannerArgs).some(
          ([argName, initialArgValue]) => {
            const currentScannerArgs = (argumentsForm as ArgumentsForm)[
              scannerName
            ];
            const scannerArgsExist = initialScannerArgs && currentScannerArgs;

            if (scannerArgsExist) {
              const currentArgValue = currentScannerArgs[argName];
              return currentArgValue !== initialArgValue;
            }
          },
        ),
    );

  const isGuardFormValid =
    invalidArguments.filter(
      (invalidScannerArgs) => invalidScannerArgs[1].length !== 0,
    ).length === 0;

  const isConfirmChangesButtonDisabled =
    !isHydrated || !isGuardFormValid || !isGuardFormModified();

  return {
    previousArgumentsValues,
    argumentsForm,
    handlers: {
      onArgumentValueChange,
      onArgumentValidityChange,
    },
    footerProps: {
      isConfirmChangesButtonDisabled,
      onConfirmChangesButtonClick,
      onCancelChangesButtonClick,
    },
  };
};

export default useGuardServiceCard;
