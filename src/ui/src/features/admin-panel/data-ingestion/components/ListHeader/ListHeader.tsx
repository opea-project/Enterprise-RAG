// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ListHeader.scss";

import classNames from "classnames";

import Button from "@/components/ui/Button/Button";

interface ListHeaderProps {
  title?: string;
  onClearListBtnClick: () => void;
}

const ListHeader = ({ title, onClearListBtnClick }: ListHeaderProps) => (
  <header
    className={classNames({
      "list-header": true,
      "justify-between": title,
    })}
  >
    {title && <h3>{title}</h3>}
    <Button color="error" size="sm" onClick={onClearListBtnClick}>
      Delete All
    </Button>
  </header>
);

export default ListHeader;
