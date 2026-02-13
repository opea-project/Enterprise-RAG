// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SourceDialog.scss";

import {
  ActionDialog,
  Button,
  Tooltip,
} from "@intel-enterprise-rag-ui/components";
import { Fragment, ReactNode } from "react";

const SOURCE_DIALOG_TITLE_CHAR_LIMIT = 50; // used to truncate long source names for dialog title

interface SourceDialogProps {
  name: string;
  triggerIcon: ReactNode;
  actionLabel: string;
  citations?: string[];
  className?: string;
  onAction: () => void;
}

export const SourceDialog = ({
  name,
  triggerIcon,
  actionLabel,
  citations,
  className,
  onAction,
}: SourceDialogProps) => {
  const trigger = (
    <Tooltip
      title="Show details"
      trigger={
        <Button className={`source-dialog__trigger ${className ?? ""}`}>
          <div className="source-dialog__trigger__icon">{triggerIcon}</div>
          <div className="source-dialog__trigger__name">{name}</div>
        </Button>
      }
    />
  );

  const title =
    name.length > SOURCE_DIALOG_TITLE_CHAR_LIMIT
      ? `${name.slice(0, SOURCE_DIALOG_TITLE_CHAR_LIMIT)}...`
      : name;

  return (
    <ActionDialog
      title={title}
      trigger={trigger}
      maxWidth={600}
      confirmLabel={actionLabel}
      cancelLabel="Close"
      onConfirm={onAction}
    >
      <div className="source-dialog__content">
        <h3 className="source-dialog__citations-header">Citations</h3>
        <div className="source-dialog__citations-list">
          {citations?.map((text, index) => (
            <Fragment key={`${title}-${index}-citation`}>
              <span className="source-dialog__citation-index">{index + 1}</span>
              <p key={index} className="source-dialog__citation-text">
                {text}
              </p>
            </Fragment>
          ))}
        </div>
      </div>
    </ActionDialog>
  );
};
