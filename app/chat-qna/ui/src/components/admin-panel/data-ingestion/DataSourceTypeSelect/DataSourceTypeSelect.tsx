// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataSourceTypeSelect.scss";

import { InputLabel, MenuItem, Select, SelectChangeEvent } from "@mui/material";

import { DataIngestionSourceType } from "@/models/dataIngestion";

interface DataSourceTypeSelectItem {
  value: DataIngestionSourceType;
  label: string;
}

const dataSourceTypeSelectItems: DataSourceTypeSelectItem[] = [
  {
    value: "documents",
    label: "Documents",
  },
  {
    value: "links",
    label: "Links",
  },
];

interface DataSourceTypeSelectProps {
  value: DataIngestionSourceType;
  onChange: (event: SelectChangeEvent<DataIngestionSourceType>) => void;
}

const DataSourceTypeSelect = ({
  value,
  onChange,
}: DataSourceTypeSelectProps) => (
  <div className="data-source-type-select-wrapper">
    <InputLabel htmlFor="data-source-type-select">Data Source Type</InputLabel>
    <Select
      value={value}
      onChange={onChange}
      className="data-source-type-select"
      inputProps={{
        id: "data-source-type-select",
      }}
    >
      {dataSourceTypeSelectItems.map(({ value, label }) => (
        <MenuItem key={`data-source-type-${value}`} value={value}>
          {label}
        </MenuItem>
      ))}
    </Select>
  </div>
);

export default DataSourceTypeSelect;
