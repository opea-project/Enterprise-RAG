// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import CloseIcon from "@mui/icons-material/Close";
import { IconButton, InputAdornment } from "@mui/material";

interface ClearInputIconButtonProps {
  disabled: boolean;
  onClick: () => void;
}

const ClearInputIconButton = ({
  disabled,
  onClick,
}: ClearInputIconButtonProps) => (
  <InputAdornment position="end">
    <IconButton disabled={disabled} onClick={onClick} edge="end">
      <CloseIcon fontSize="small" />
    </IconButton>
  </InputAdornment>
);

export default ClearInputIconButton;
