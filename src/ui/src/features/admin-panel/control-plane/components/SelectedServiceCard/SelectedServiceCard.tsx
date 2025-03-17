// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SelectedServiceCard.scss";

import classNames from "classnames";
import { Fragment, MouseEventHandler, PropsWithChildren } from "react";

import Button from "@/components/ui/Button/Button";
import ServiceStatusIndicator from "@/features/admin-panel/control-plane/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import {
  ServiceDetails,
  ServiceStatus,
} from "@/features/admin-panel/control-plane/types";
import { useAppSelector } from "@/store/hooks";

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
      "h-[calc(100vh-11.5rem)]": !footerProps,
      "h-[calc(100vh-13.75rem)]": footerProps,
    },
  ]);

  return (
    <div className="selected-service-card">
      <div className="selected-service-card__wrapper">
        <div>
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
        </div>
        {footerProps && <SelectedServiceCardFooter {...footerProps} />}
      </div>
    </div>
  );
};

const formatLabel = (label: string) =>
  label
    .split("_")
    .map((word) => {
      if (["LLM", "DB"].includes(word)) {
        return word;
      }

      word = word.toLowerCase();
      return `${word.slice(0, 1).toUpperCase()}${word.slice(1)}`;
    })
    .join(" ");

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
          <p className="service-detail-label">{formatLabel(label)}</p>
          <p className="service-detail-value">{value}</p>
        </Fragment>
      ))}
    </section>
  );
};

interface SelectedServiceCardFooterProps {
  isConfirmChangesButtonDisabled: boolean;
  onConfirmChangesButtonClick: MouseEventHandler;
  onCancelChangesButtonClick: MouseEventHandler;
  onEditArgumentsButtonClick: MouseEventHandler;
}

const SelectedServiceCardFooter = ({
  isConfirmChangesButtonDisabled,
  onConfirmChangesButtonClick,
  onCancelChangesButtonClick,
  onEditArgumentsButtonClick,
}: SelectedServiceCardFooterProps) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);

  const ConfirmChangesButton = (
    <Button
      size="sm"
      color="success"
      fullWidth
      disabled={isConfirmChangesButtonDisabled}
      onClick={onConfirmChangesButtonClick}
    >
      Confirm Changes
    </Button>
  );

  const CancelChangesButton = (
    <Button
      size="sm"
      variant="outlined"
      fullWidth
      onClick={onCancelChangesButtonClick}
    >
      Cancel
    </Button>
  );

  const EditServiceArgumentsButton = (
    <Button size="sm" fullWidth onClick={onEditArgumentsButtonClick}>
      Edit Service Arguments
    </Button>
  );

  const actionButtons = isEditModeEnabled ? (
    <>
      {ConfirmChangesButton}
      {CancelChangesButton}
    </>
  ) : (
    EditServiceArgumentsButton
  );

  return (
    <footer className="selected-service-card__footer">{actionButtons}</footer>
  );
};

export default SelectedServiceCard;
