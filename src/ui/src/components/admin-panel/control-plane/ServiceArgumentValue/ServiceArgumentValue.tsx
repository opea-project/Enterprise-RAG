// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactElement } from "react";

import ServiceArgumentCheckbox from "@/components/admin-panel/control-plane/ServiceArgumentCheckbox/ServiceArgumentCheckbox";
import ServiceArgumentNumberInput from "@/components/admin-panel/control-plane/ServiceArgumentNumberInput/ServiceArgumentNumberInput";
import ServiceArgumentTextInput from "@/components/admin-panel/control-plane/ServiceArgumentTextInput/ServiceArgumentTextInput";
import ThreeStateSwitch from "@/components/shared/ThreeStateSwitch/ThreeStateSwitch";
import ServiceArgument, {
  ServiceArgumentInputValue,
} from "@/models/admin-panel/control-plane/serviceArgument";
import { chatQnAGraphEditModeEnabledSelector } from "@/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

interface ServiceArgumentValueProps {
  argumentData: ServiceArgument;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: ServiceArgumentInputValue,
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
  const { displayName, value, range, type, nullable, commaSeparated } =
    argumentData;

  const editModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  let argumentValue: ReactElement | null = null;

  if (type === "text") {
    if (typeof value === "string" || (value === null && nullable)) {
      argumentValue = (
        <ServiceArgumentTextInput
          name={displayName}
          initialValue={value}
          emptyValueAllowed={nullable}
          commaSeparated={commaSeparated}
          readOnly={!editModeEnabled}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      );
    }
  }

  if (type === "boolean") {
    if (typeof value === "boolean" && !nullable) {
      argumentValue = (
        <ServiceArgumentCheckbox
          name={displayName}
          initialValue={value}
          readOnly={!editModeEnabled}
          onArgumentValueChange={onArgumentValueChange}
        />
      );
    } else if ((typeof value === "boolean" && nullable) || value === null) {
      const handleChange = (newValue: boolean | null) => {
        onArgumentValueChange(displayName, newValue);
      };

      argumentValue = (
        <ThreeStateSwitch
          initialValue={value}
          readOnly={!editModeEnabled}
          name={displayName}
          onChange={handleChange}
        />
      );
    }
  }

  if (type === "number") {
    const isValidNotNullable = typeof value === "number" && range;
    const isNullable = value === null && nullable && range;
    if (isValidNotNullable || isNullable) {
      argumentValue = (
        <ServiceArgumentNumberInput
          name={displayName}
          initialValue={value}
          nullable={nullable}
          readOnly={!editModeEnabled}
          range={range}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      );
    }
  }

  return <div>{argumentValue}</div>;
};

export default ServiceArgumentValue;
