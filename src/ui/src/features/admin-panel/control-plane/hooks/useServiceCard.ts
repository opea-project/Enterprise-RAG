// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useCallback, useEffect, useState } from "react";

import { useChangeArgumentsMutation } from "@/features/admin-panel/control-plane/api";
import { setChatQnAGraphIsEditModeEnabled } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  OnArgumentValidityChangeHandler,
  OnArgumentValueChangeHandler,
} from "@/features/admin-panel/control-plane/types";
import { ChangeArgumentsRequestData } from "@/features/admin-panel/control-plane/types/api";
import { useAppDispatch } from "@/store/hooks";

export type FilterFormDataFunction<T> = (formData: T) => Partial<T>;
export type FilterInvalidArgumentsFunction<T> = (
  invalidArguments: string[],
  formData: T,
) => string[];

const useServiceCard = <T>(
  serviceName: string,
  args?: T,
  filterFns?: {
    filterFormData: FilterFormDataFunction<T>;
    filterInvalidArguments: FilterInvalidArgumentsFunction<T>;
  },
) => {
  const dispatch = useAppDispatch();
  const [changeArguments] = useChangeArgumentsMutation();

  const [invalidArguments, setInvalidArguments] = useState<string[]>([]);
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

  const onEditArgumentsButtonClick = () => {
    dispatch(setChatQnAGraphIsEditModeEnabled(true));
  };

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
    setArgumentsForm((prevForm) => {
      const newForm = { ...prevForm };
      for (const argumentName in newForm) {
        newForm[argumentName] = previousArgumentsValues[argumentName];
      }
      return newForm;
    });
    setInvalidArguments([]);
    dispatch(setChatQnAGraphIsEditModeEnabled(false));
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
    !isServiceFormValid() || !isServiceFormModified();

  return {
    argumentsForm,
    previousArgumentsValues,
    onArgumentValueChange,
    onArgumentValidityChange,
    footerProps: {
      isConfirmChangesButtonDisabled,
      onEditArgumentsButtonClick,
      onConfirmChangesButtonClick,
      onCancelChangesButtonClick,
    },
  };
};

export default useServiceCard;
