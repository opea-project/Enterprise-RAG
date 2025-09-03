// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SelectedServiceCard.scss";

import classNames from "classnames";
import { Fragment, PropsWithChildren } from "react";
import { PressEvent } from "react-aria-components";

import Button from "@/components/ui/Button/Button";
import ServiceStatusIndicator from "@/features/admin-panel/control-plane/components/ServiceStatusIndicator/ServiceStatusIndicator";
import {
  ServiceDetails,
  ServiceStatus,
} from "@/features/admin-panel/control-plane/types";

interface SelectedServiceCardProps extends PropsWithChildren {
  serviceStatus?: ServiceStatus;
  serviceName: string;
  serviceDetails?: ServiceDetails;
  footerProps?: SelectedServiceCardFooterProps;
  DebugDialog?: JSX.Element;
}

const SelectedServiceCard = ({
  serviceStatus,
  serviceName,
  serviceDetails,
  footerProps,
  DebugDialog,
  children,
}: SelectedServiceCardProps) => {
  const contentClassNames = classNames([
    "selected-service-card__content",
    {
      "h-[calc(100vh-10.75rem)]": !footerProps,
      "h-[calc(100vh-12.75rem)]": footerProps,
    },
  ]);

  return (
    <div className="selected-service-card">
      <div className="selected-service-card__wrapper">
        <header className="selected-service-card__header">
          <ServiceStatusIndicator status={serviceStatus} />
          <p className="selected-service-card__header__service-name">
            {serviceName}
          </p>
          {DebugDialog}
        </header>
        <div className={contentClassNames}>
          {serviceDetails && (
            <ServiceDetailsGrid serviceDetails={serviceDetails} />
          )}
          {children}
        </div>
        {footerProps && <SelectedServiceCardFooter {...footerProps} />}
      </div>
    </div>
  );
};

interface ServiceDetailsGridProps {
  serviceDetails?: ServiceDetails;
}

const ServiceDetailsGrid = ({ serviceDetails }: ServiceDetailsGridProps) => {
  if (!serviceDetails) {
    return null;
  }

  return (
    <section className="service-details-grid">
      {Object.entries(serviceDetails).map(([label, value]) => (
        <Fragment key={label}>
          <p className="service-detail-label">{label}</p>
          <p className="service-detail-value">{value}</p>
        </Fragment>
      ))}
    </section>
  );
};

interface SelectedServiceCardFooterProps {
  isConfirmChangesButtonDisabled: boolean;
  onConfirmChangesButtonClick: (event: PressEvent) => void;
  onCancelChangesButtonClick: (event: PressEvent) => void;
}

const SelectedServiceCardFooter = ({
  isConfirmChangesButtonDisabled,
  onConfirmChangesButtonClick,
  onCancelChangesButtonClick,
}: SelectedServiceCardFooterProps) => {
  return (
    <footer className="selected-service-card__footer">
      <Button
        size="sm"
        color="success"
        fullWidth
        isDisabled={isConfirmChangesButtonDisabled}
        onPress={onConfirmChangesButtonClick}
      >
        Confirm Changes
      </Button>
      <Button
        size="sm"
        variant="outlined"
        fullWidth
        isDisabled={isConfirmChangesButtonDisabled}
        onPress={onCancelChangesButtonClick}
      >
        Cancel
      </Button>
    </footer>
  );
};

export default SelectedServiceCard;
