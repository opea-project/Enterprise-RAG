// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentValue.scss";

import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentTextInput from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";
import { chatQnAGraphEditModeEnabledSelector } from "@/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

interface ServiceArgumentValueProps {
  argumentData: ServiceArgument;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: string | number | boolean | null,
  ) => void;
  onArgumentValidityChange: (
    argumentName: string,
    isArgumentInvalid: boolean,
  ) => void;
}

const ServiceArgumentValue = ({
  argumentData,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentValueProps) => {
  const { displayName, value, range, type, nullable } = argumentData;

  const editModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  let argumentValue = <></>;

  if (typeof value === "string") {
    if (editModeEnabled) {
      argumentValue = (
        <ServiceArgumentTextInput
          name={displayName}
          initialValue={value}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      );
    } else {
      argumentValue = <p className="service-argument-value">{value}</p>;
    }
  }
  if (typeof value === "number" && range) {
    if (editModeEnabled) {
      argumentValue = (
        <ServiceArgumentNumberInput
          name={displayName}
          initialValue={value}
          nullable={nullable}
          range={range}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      );
    } else {
      argumentValue = <p className="service-argument-value">{value}</p>;
    }
  }
  if (typeof value === "boolean") {
    argumentValue = (
      <ServiceArgumentCheckbox
        name={displayName}
        initialValue={value}
        onArgumentValueChange={onArgumentValueChange}
      />
    );
  }
  if (value === null) {
    if (editModeEnabled) {
      if (type === "text") {
        argumentValue = (
          <ServiceArgumentTextInput
            name={displayName}
            initialValue={""}
            onArgumentValueChange={onArgumentValueChange}
            onArgumentValidityChange={onArgumentValidityChange}
          />
        );
      } else if (type === "number" && range) {
        argumentValue = (
          <ServiceArgumentNumberInput
            name={displayName}
            initialValue={value}
            nullable={nullable}
            range={range}
            onArgumentValueChange={onArgumentValueChange}
            onArgumentValidityChange={onArgumentValidityChange}
          />
        );
      }
    } else {
      argumentValue = <p className="service-argument-value">not used</p>;
    }
  }

  return argumentValue;
};

export default ServiceArgumentValue;
