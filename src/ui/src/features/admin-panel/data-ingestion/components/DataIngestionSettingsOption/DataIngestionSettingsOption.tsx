// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from "react";

interface DataIngestionSettingsOptionProps {
  name: string;
  input: ReactNode;
  description: string;
}

const DataIngestionSettingsOption = ({
  name,
  input,
  description,
}: DataIngestionSettingsOptionProps) => (
  <>
    <p className="text-xs font-medium">{name}</p>
    {input}
    <p className="text-xs">{description}</p>
  </>
);

export default DataIngestionSettingsOption;
