// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Typography } from "@mui/material";

import InfoAlert from "@/components/shared/InfoAlert/InfoAlert";

const DataIngestionInfoAlert = () => (
  <InfoAlert localStorageShowKey="showAdminPanelDataIngestionInfo">
    <Typography variant="body2">
      Select <b>Data Source Type</b> by using the dropdown below.
    </Typography>
    <Typography variant="body2">
      Depending on the selected <b>Data Source Type</b> you can either upload{" "}
      <b>Documents</b> from your local machine or provide a list of <b>Links</b>{" "}
      to external data sources.
    </Typography>
    <Typography variant="body2">
      In order to send data you want to be ingested, click <b>Upload Data</b>{" "}
      button placed at the bottom right corner of this page.
    </Typography>
  </InfoAlert>
);

export default DataIngestionInfoAlert;
