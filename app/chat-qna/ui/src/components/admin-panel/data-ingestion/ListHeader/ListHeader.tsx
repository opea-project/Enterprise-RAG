// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ListHeader.scss";

import { Button, Typography } from "@mui/material";

interface ListHeaderProps {
  title?: string;
  clearListBtnDisabled: boolean;
  onClearListBtnClick: () => void;
}

const ListHeader = ({
  title,
  clearListBtnDisabled,
  onClearListBtnClick,
}: ListHeaderProps) => (
  <header className={`list-header ${title ? "with-title" : ""}`}>
    {title && <Typography variant="h2">{title}</Typography>}
    <Button
      disabled={clearListBtnDisabled}
      color="error"
      size="small"
      onClick={onClearListBtnClick}
    >
      Clear List
    </Button>
  </header>
);

export default ListHeader;
