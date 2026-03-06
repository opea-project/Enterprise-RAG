// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./GraphControls.scss";

import {
  Button,
  CheckboxInput,
  CheckboxInputChangeHandler,
} from "@intel-enterprise-rag-ui/components";
import { ConfigurableServiceIcon } from "@intel-enterprise-rag-ui/icons";

import { ServiceStatusIndicator } from "@/components/ServiceStatusIndicator/ServiceStatusIndicator";
import { ServiceStatus } from "@/types/index";

interface GraphControlsProps {
  isAutorefreshEnabled: boolean;
  onAutorefreshChange: CheckboxInputChangeHandler;
  onRefresh: () => void;
  isFetching: boolean;
}

export const GraphControls = ({
  isAutorefreshEnabled,
  onAutorefreshChange,
  onRefresh,
  isFetching,
}: GraphControlsProps) => {
  const buttonText = isFetching ? "Refreshing..." : "Refresh";

  return (
    <div className="graph-controls" data-testid="graph-controls">
      <div className="graph-controls__legend">
        <div className="graph-controls__legend-item">
          <ServiceStatusIndicator status={ServiceStatus.Ready} noTooltip />
          <p className="graph-controls__legend-label">Ready</p>
        </div>
        <div className="graph-controls__legend-item">
          <ServiceStatusIndicator status={ServiceStatus.NotReady} noTooltip />
          <p className="graph-controls__legend-label">Not Ready</p>
        </div>
        <div className="graph-controls__legend-item">
          <ServiceStatusIndicator
            status={ServiceStatus.NotAvailable}
            noTooltip
          />
          <p className="graph-controls__legend-label">Status Not Available</p>
        </div>
        <div className="graph-controls__legend-item">
          <ConfigurableServiceIcon fontSize={12} />
          <p className="graph-controls__legend-label">Configurable Service</p>
        </div>
      </div>
      <div className="graph-controls__actions">
        <div className="graph-controls__actions-item">
          <CheckboxInput
            name="control-plane-autorefresh"
            label="Autorefresh Status"
            size="sm"
            isSelected={isAutorefreshEnabled}
            onChange={onAutorefreshChange}
            data-testid="control-plane-autorefresh-checkbox"
            dense
          />
        </div>
        <div className="graph-controls__actions-item">
          <Button
            icon="refresh"
            size="sm"
            variant="outlined"
            onPress={onRefresh}
            isDisabled={isFetching}
            data-testid="control-plane-refresh-button"
          >
            {buttonText}
          </Button>
        </div>
      </div>
    </div>
  );
};
