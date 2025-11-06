// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button } from "@intel-enterprise-rag-ui/components";
import { ExportIcon } from "@intel-enterprise-rag-ui/icons";

interface ExportButtonProps {
  onPress: () => void;
  className?: string;
}

const ExportButton = ({ onPress, className }: ExportButtonProps) => (
  <Button
    variant="outlined"
    size="sm"
    className={`flex items-center gap-2 ${className ?? ""}`}
    onPress={onPress}
  >
    <ExportIcon />
    Export
  </Button>
);

export default ExportButton;
