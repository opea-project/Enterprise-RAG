// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import CheckboxInput from "@/components/ui/CheckboxInput/CheckboxInput";
import DataIngestionSettingsOption from "@/features/admin-panel/data-ingestion/components/DataIngestionSettingsOption/DataIngestionSettingsOption";
import {
  END_DATA_STATUSES,
  POLLING_INTERVAL,
} from "@/features/admin-panel/data-ingestion/config/api";
import {
  selectIsAutorefreshEnabled,
  setIsAutorefreshEnabled,
} from "@/features/admin-panel/data-ingestion/store/dataIngestionSettings.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { titleCaseString } from "@/utils";

const pollingIntervalInSeconds = POLLING_INTERVAL / 1000;

const titleCasedStatuses = END_DATA_STATUSES.map((status) =>
  titleCaseString(status),
).join(", ");

const getDescription = (isAutorefreshEnabled: boolean) =>
  isAutorefreshEnabled
    ? `Automatic data refresh occurs every ${pollingIntervalInSeconds} seconds until all data objects reach one of the following statuses: ${titleCasedStatuses}.`
    : "Autorefresh is currently disabled. Data will not be automatically refreshed.";

const AutorefreshSettingsOption = () => {
  const isAutorefreshEnabled = useAppSelector(selectIsAutorefreshEnabled);
  const dispatch = useAppDispatch();

  const handleChange = (isSelected: boolean) => {
    dispatch(setIsAutorefreshEnabled(isSelected));
  };

  const label = isAutorefreshEnabled ? "Enabled" : "Disabled";
  const description = getDescription(isAutorefreshEnabled);

  return (
    <DataIngestionSettingsOption
      name="Autorefresh"
      input={
        <CheckboxInput
          name="data-ingestion-autorefresh"
          label={label}
          size="sm"
          dense
          isSelected={isAutorefreshEnabled}
          onChange={handleChange}
        />
      }
      description={description}
    />
  );
};

export default AutorefreshSettingsOption;
