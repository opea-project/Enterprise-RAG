// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SourceItem.scss";

import { ReactNode } from "react";

import Tooltip from "@/components/ui/Tooltip/Tooltip";

interface SourceItemProps {
  icon: ReactNode;
  name: string;
  actions?: ReactNode;
  className?: string;
}

const SourceItem = ({ icon, name, actions, className }: SourceItemProps) => (
  <Tooltip
    title={name}
    trigger={
      <div className={`source-item ${className ?? ""}`}>
        <div className="source-item__icon">{icon}</div>
        <div className="source-item__name">{name}</div>
        {actions && <div className="source-item__actions">{actions}</div>}
      </div>
    }
  />
);

export default SourceItem;
