// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentValue.scss";

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

  let argumentValue = <p className="service-argument-value">{value}</p>;

  if (type === "text") {
    if (editModeEnabled) {
      if (typeof value === "string" || (value === null && nullable)) {
        argumentValue = (
          <ServiceArgumentTextInput
            name={displayName}
            initialValue={value}
            emptyValueAllowed={nullable}
            commaSeparated={commaSeparated}
            onArgumentValueChange={onArgumentValueChange}
            onArgumentValidityChange={onArgumentValidityChange}
          />
        );
      }
    } else {
      const valueText = value === null ? "not set" : value.toString();
      argumentValue = <p className="service-argument-value">{valueText}</p>;
    }
  }

  if (type === "boolean") {
    if (editModeEnabled) {
      if (typeof value === "boolean" && !nullable) {
        argumentValue = (
          <ServiceArgumentCheckbox
            name={displayName}
            initialValue={value}
            onArgumentValueChange={onArgumentValueChange}
          />
        );
      } else if ((typeof value === "boolean" && nullable) || value === null) {
        const handleChange = (newValue: boolean | null) => {
          onArgumentValueChange(displayName, newValue);
        };

        argumentValue = (
          <ThreeStateSwitch initialValue={value} onChange={handleChange} />
        );
      }
    } else {
      const valueText = value === null ? "not set" : value.toString();
      argumentValue = <p className="service-argument-value">{valueText}</p>;
    }
  }

  if (type === "number") {
    const isValidNotNullable = typeof value === "number" && range;
    const isNullable = value === null && nullable && range;
    if (editModeEnabled && (isValidNotNullable || isNullable)) {
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
      const valueText = value === null ? "not set" : value;
      argumentValue = <p className="service-argument-value">{valueText}</p>;
    }
  }

  return argumentValue;
};

export default ServiceArgumentValue;
