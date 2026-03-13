// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SelectedServiceCard.scss";

import { Button } from "@intel-enterprise-rag-ui/components";
import classNames from "classnames";
import { Fragment, PropsWithChildren, ReactNode } from "react";
import { PressEvent } from "react-aria-components";

import { ServiceStatusIndicator } from "@/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceDetails, ServiceStatus } from "@/types/index";

export interface SelectedServiceCardFooterProps {
  isConfirmChangesButtonDisabled: boolean;
  onConfirmChangesButtonClick: (event: PressEvent) => void;
  onCancelChangesButtonClick: (event: PressEvent) => void;
}

export interface SelectedServiceCardProps extends PropsWithChildren {
  serviceStatus?: ServiceStatus;
  serviceName: string;
  serviceDetails?: ServiceDetails;
  footerProps?: SelectedServiceCardFooterProps;
  DebugDialog?: ReactNode;
}

export const SelectedServiceCard = ({
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
      "selected-service-card__content--no-footer": !footerProps,
      "selected-service-card__content--with-footer": footerProps,
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

const SelectedServiceCardFooter = ({
  isConfirmChangesButtonDisabled,
  onConfirmChangesButtonClick,
  onCancelChangesButtonClick,
}: SelectedServiceCardFooterProps) => (
  <footer className="selected-service-card__footer">
    <Button
      data-testid="confirm-service-changes-button"
      size="sm"
      color="success"
      isDisabled={isConfirmChangesButtonDisabled}
      onPress={onConfirmChangesButtonClick}
      fullWidth
    >
      Confirm Changes
    </Button>
    <Button
      data-testid="cancel-service-changes-button"
      size="sm"
      variant="outlined"
      isDisabled={isConfirmChangesButtonDisabled}
      onPress={onCancelChangesButtonClick}
      fullWidth
    >
      Cancel
    </Button>
  </footer>
);
