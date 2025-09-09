// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Switch } from "@intel-enterprise-rag-ui/components";

import DataIngestionSettingsOption from "@/features/admin-panel/data-ingestion/components/DataIngestionSettingsOption/DataIngestionSettingsOption";
import useProcessingTimeFormat from "@/features/admin-panel/data-ingestion/hooks/useProcessingTimeFormat";

const options = {
  standard: {
    label: "Standard",
    description: "Standard time format (00:00:06.239 for 6239 milliseconds)",
  },
  compact: {
    label: "Compact",
    description:
      "Format displaying only non-zero units (6s 239ms for 6239 milliseconds)",
  },
};

const ProcessingTimeFormatSettingsOption = () => {
  const { processingTimeFormat, setFormat } = useProcessingTimeFormat();

  const isCompactFormat = processingTimeFormat === "compact";

  const handleChange = (isSelected: boolean) => {
    setFormat(isSelected ? "compact" : "standard");
  };

  return (
    <DataIngestionSettingsOption
      name="Processing Time Format"
      input={
        <div className="flex items-center gap-2">
          <span className="text-xs">{options.standard.label}</span>
          <Switch isSelected={isCompactFormat} onChange={handleChange} />
          <span className="text-xs">{options.compact.label}</span>
        </div>
      }
      description={options[processingTimeFormat].description}
    />
  );
};
export default ProcessingTimeFormatSettingsOption;
