// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import { ChangeArgumentsRequestData } from "@/api/models/systemFingerprint";
import {
  changeServiceArguments,
  setChatQnAGraphEditMode,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch } from "@/store/hooks";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
  ServiceArgumentInputValue,
} from "@/types/admin-panel/control-plane";

type ArgumentsForm = Record<string, Record<string, ServiceArgumentInputValue>>;

const useGuardServiceCard = <T>(guardName: string, args?: T) => {
  const dispatch = useAppDispatch();

  const [invalidArguments, setInvalidArguments] = useState<
    [string, string[]][]
  >([]);
  const [argumentsForm, setArgumentsForm] = useState<T>({} as T);
  const [previousArgumentsValues, setPreviousArgumentsValues] = useState<T>(
    args as T,
  );

  useEffect(() => {
    if (args !== undefined) {
      setArgumentsForm(args as T);
      setPreviousArgumentsValues(args as T);
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

  const onEditArgumentsButtonClick = () => {
    dispatch(setChatQnAGraphEditMode(true));
  };

  const onConfirmChangesButtonClick = () => {
    dispatch(
      changeServiceArguments({
        name: guardName,
        data: argumentsForm as ChangeArgumentsRequestData,
      }),
    );
  };

  const onCancelChangesButtonClick = () => {
    setArgumentsForm(previousArgumentsValues);
    setInvalidArguments([]);
    dispatch(setChatQnAGraphEditMode(false));
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
    !isGuardFormValid || !isGuardFormModified();

  return {
    previousArgumentsValues,
    handlers: {
      onArgumentValueChange,
      onArgumentValidityChange,
    },
    footerProps: {
      isConfirmChangesButtonDisabled,
      onEditArgumentsButtonClick,
      onConfirmChangesButtonClick,
      onCancelChangesButtonClick,
    },
  };
};

export default useGuardServiceCard;
