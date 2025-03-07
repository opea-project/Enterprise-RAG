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
} from "@/types/admin-panel/control-plane";

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
    dispatch(setChatQnAGraphEditMode(true));
  };

  const onConfirmChangesButtonClick = () => {
    let data: Partial<T> = argumentsForm;
    if (filterFns && filterFns.filterFormData) {
      data = filterFns.filterFormData(argumentsForm);
    }

    dispatch(
      changeServiceArguments({
        name: serviceName,
        data: data as ChangeArgumentsRequestData,
      }),
    );
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
    dispatch(setChatQnAGraphEditMode(false));
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
