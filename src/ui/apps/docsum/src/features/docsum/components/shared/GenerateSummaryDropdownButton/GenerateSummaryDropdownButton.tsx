// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { DropdownButton } from "@intel-enterprise-rag-ui/components";

import { SummaryType } from "@/features/docsum/api/types";

const SUMMARY_TYPE_OPTIONS: { value: SummaryType; label: string }[] = [
  { value: "map_reduce", label: "Map Reduce" },
  { value: "stuff", label: "Stuff" },
  { value: "refine", label: "Refine" },
];

interface GenerateSummaryDropdownButtonProps {
  summaryType: SummaryType;
  onSummaryTypeChange: (value: SummaryType) => void;
  onGenerateSummary: () => void;
  isDisabled: boolean;
  className?: string;
}

const GenerateSummaryDropdownButton = ({
  summaryType,
  onSummaryTypeChange,
  onGenerateSummary,
  isDisabled,
  className,
}: GenerateSummaryDropdownButtonProps) => (
  <DropdownButton
    label="Generate Summary"
    selectedValue={summaryType}
    options={SUMMARY_TYPE_OPTIONS}
    onPress={onGenerateSummary}
    onSelectionChange={(value) => onSummaryTypeChange(value as SummaryType)}
    isDisabled={isDisabled}
    ariaLabel="Change summarization strategy"
    className={className}
  />
);

export default GenerateSummaryDropdownButton;
