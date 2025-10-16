// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from "@intel-enterprise-rag-ui/components";

interface GenerateSummaryButtonProps {
  isDisabled: boolean;
  onPress: () => void;
}

const GenerateSummaryButton = ({
  isDisabled,
  onPress,
}: GenerateSummaryButtonProps) => (
  <Button
    isDisabled={isDisabled}
    className="mt-4"
    aria-label="Generate Summary"
    onPress={onPress}
  >
    Generate Summary
  </Button>
);

export default GenerateSummaryButton;
