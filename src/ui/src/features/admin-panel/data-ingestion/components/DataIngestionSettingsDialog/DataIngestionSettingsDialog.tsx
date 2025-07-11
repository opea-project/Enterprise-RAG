// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataIngestionSettingsDialog.scss";

import Dialog from "@/components/ui/Dialog/Dialog";
import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";
import AutorefreshSettingsOption from "@/features/admin-panel/data-ingestion/components/AutorefreshSettingsOption/AutorefreshSettingsOption";
import ProcessingTimeFormatSettingsOption from "@/features/admin-panel/data-ingestion/components/ProcessingTimeFormatSettingsOption/ProcessingTimeFormatSettingsOption";

const DataIngestionSettingsDialog = () => (
  <Dialog
    trigger={
      <Tooltip title="Settings" trigger={<IconButton icon="settings" />} />
    }
    title="Settings"
    maxWidth={800}
    isCentered
  >
    <div className="data-ingestion-settings">
      <AutorefreshSettingsOption />
      <ProcessingTimeFormatSettingsOption />
    </div>
  </Dialog>
);

export default DataIngestionSettingsDialog;
