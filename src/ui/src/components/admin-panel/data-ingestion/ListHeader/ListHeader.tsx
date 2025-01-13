// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ListHeader.scss";

import classNames from "classnames";

interface ListHeaderProps {
  title?: string;
  disabled: boolean;
  onClearListBtnClick: () => void;
}

const ListHeader = ({
  title,
  disabled,
  onClearListBtnClick,
}: ListHeaderProps) => (
  <header
    className={classNames({
      "list-header": true,
      "justify-between": title,
    })}
  >
    {title && <h3>{title}</h3>}
    <button
      className="outlined-button--danger"
      disabled={disabled}
      onClick={onClearListBtnClick}
    >
      Clear List
    </button>
  </header>
);

export default ListHeader;
