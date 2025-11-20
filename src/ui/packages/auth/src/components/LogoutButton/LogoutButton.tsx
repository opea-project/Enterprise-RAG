// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { PressEvent } from "react-aria-components";

interface LogoutButtonProps {
  onPress: (e: PressEvent) => void;
}

export const LogoutButton = ({ onPress }: LogoutButtonProps) => (
  <Tooltip
    title="Logout"
    trigger={<IconButton icon="logout" aria-label="Logout" onPress={onPress} />}
    placement="bottom"
  />
);
