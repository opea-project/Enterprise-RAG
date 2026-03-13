// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import type { ChangeArgumentsRequestData } from "@/types/api/requests";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/types/index";

export type FilterFormDataFunction<T> = (formData: T) => Partial<T>;
export type FilterInvalidArgumentsFunction<T> = (
  invalidArguments: string[],
  formData: T,
) => string[];

export interface ServiceArgumentChange {
  name: string;
  data: ChangeArgumentsRequestData;
}

export type ChangeArgumentsFunction = (
  request: ServiceArgumentChange[],
) => void;

export interface UseServiceCardOptions<T> {
  changeArguments: ChangeArgumentsFunction;
  filterFns?: {
    filterFormData: FilterFormDataFunction<T>;
    filterInvalidArguments: FilterInvalidArgumentsFunction<T>;
  };
}

export const useServiceCard = <T>(
  serviceName: string,
  args: T | undefined,
  options: UseServiceCardOptions<T>,
) => {
  const { changeArguments, filterFns } = options;

  const [invalidArguments, setInvalidArguments] = useState<string[]>([]);
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

  const onArgumentValueChange: OnArgumentValueChangeHandler = (
    argumentName,
    argumentValue,
  ) => {
    setArgumentsForm((prevArguments) => ({
      ...prevArguments,
      [argumentName]: argumentValue,
    }));
  };

  const onArgumentValidityChange: OnArgumentValidityChangeHandler = useCallback(
    (argumentName, isArgumentInvalid) => {
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

  const onConfirmChangesButtonClick = () => {
    let data: Partial<T> = argumentsForm;
    if (filterFns && filterFns.filterFormData) {
      data = filterFns.filterFormData(argumentsForm);
    }

    const changeArgumentsRequest = [
      {
        name: serviceName,
        data: data as ChangeArgumentsRequestData,
      },
    ];

    changeArguments(changeArgumentsRequest);
  };

  const onCancelChangesButtonClick = () => {
    setArgumentsForm(previousArgumentsValues);
    setInvalidArguments([]);
  };

  const isServiceFormModified = () => {
    const changes = [];
    let initialValues: Partial<T> = { ...previousArgumentsValues };
    let currentValues: Partial<T> = { ...argumentsForm };
    if (filterFns && filterFns.filterFormData) {
      initialValues = filterFns.filterFormData(previousArgumentsValues);
      currentValues = filterFns.filterFormData(currentValues as T);
    }

    for (const argumentName in previousArgumentsValues) {
      const initialValue = initialValues[argumentName];
      const currentValue = currentValues[argumentName];
      if (initialValue !== currentValue) {
        changes.push(argumentName);
      }
    }
    return changes.length > 0;
  };

  const isServiceFormValid = () => {
    let invalidArgumentsCopy = [...invalidArguments];
    if (filterFns && filterFns.filterInvalidArguments) {
      invalidArgumentsCopy = filterFns.filterInvalidArguments(
        invalidArgumentsCopy,
        argumentsForm,
      );
    }

    return invalidArgumentsCopy.length === 0;
  };

  const isConfirmChangesButtonDisabled =
    !isHydrated || !isServiceFormValid() || !isServiceFormModified();

  return {
    argumentsForm,
    previousArgumentsValues,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps: {
      isConfirmChangesButtonDisabled,
      onConfirmChangesButtonClick,
      onCancelChangesButtonClick,
    },
  };
};
