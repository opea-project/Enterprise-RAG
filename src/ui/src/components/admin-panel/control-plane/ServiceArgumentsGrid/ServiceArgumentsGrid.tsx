// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ServiceArgumentsGrid.scss";

import ServiceArgumentValue from "@/components/admin-panel/control-plane/ServiceArgumentValue/ServiceArgumentValue";
import { ServiceArgumentsGridValues } from "@/components/admin-panel/control-plane/ServiceDetailsModalContent/ServiceDetailsModalContent";
import { ServiceArgumentInputValue } from "@/models/admin-panel/control-plane/serviceArgument";

interface ServiceArgumentsGridProps {
  argumentsGridValues: ServiceArgumentsGridValues;
  onArgumentValueChange: (
    argumentName: string,
    argumentValue: ServiceArgumentInputValue,
  ) => void;
  onArgumentValidityChange: (
    argumentName: string,
    isArgumentInvalid: boolean,
  ) => void;
}

const ServiceArgumentsGrid = ({
  argumentsGridValues,
  onArgumentValueChange,
  onArgumentValidityChange,
}: ServiceArgumentsGridProps) => (
  <div>
    <p className="service-arguments-grid-header">Service Arguments</p>
    <div className="service-arguments-grid">
      {Object.entries(argumentsGridValues.data).map(([name, argumentData]) => (
        <ServiceArgumentValue
          key={name}
          argumentData={argumentData}
          onArgumentValueChange={onArgumentValueChange}
          onArgumentValidityChange={onArgumentValidityChange}
        />
      ))}
    </div>
  </div>
);

export default ServiceArgumentsGrid;
