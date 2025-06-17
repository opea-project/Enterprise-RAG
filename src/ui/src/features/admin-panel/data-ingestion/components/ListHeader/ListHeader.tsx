// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ListHeader.scss";

import classNames from "classnames";

import Button from "@/components/ui/Button/Button";

interface ListHeaderProps {
  title?: string;
  onClearListBtnPress: () => void;
}

const ListHeader = ({ title, onClearListBtnPress }: ListHeaderProps) => (
  <header
    className={classNames({
      "list-header": true,
      "justify-between": title,
    })}
  >
    {title && <h3>{title}</h3>}
    <Button color="error" size="sm" onPress={onClearListBtnPress}>
      Delete All
    </Button>
  </header>
);

export default ListHeader;
