// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ThreeStateSwitch.scss";

import classNames from "classnames";
import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";

interface ThreeStateSwitchProps {
  initialValue?: boolean | null;
  name: string;
  readOnly?: boolean;
  onChange?: (value: boolean | null) => void;
}

const ThreeStateSwitch = ({
  initialValue = null,
  name,
  readOnly,
  onChange,
}: ThreeStateSwitchProps) => {
  const [state, setState] = useState(initialValue);

  useEffect(() => {
    if (readOnly) {
      setState(initialValue);
    }
  }, [readOnly, initialValue]);

  const handleBtnClick = (value: boolean | null) => {
    if (!readOnly) {
      setState(value);
      if (onChange) {
        onChange(value);
      }
    }
  };

  const trueBtnClassNames = classNames({
    "three-state-switch__button": true,
    "three-state-switch__button--active": state === true,
  });

  const falseBtnClassNames = classNames({
    "three-state-switch__button": true,
    "three-state-switch__button--active": state === false,
  });

  const nullBtnClassNames = classNames({
    "three-state-switch__button": true,
    "three-state-switch__button--active": state === null,
  });

  const switchClassNames = classNames(
    {
      "three-state-switch--read-only": readOnly,
    },
    "three-state-switch",
  );

  const switchId = `${name}-three-state-switch-${uuidv4()}`;

  return (
    <div>
      <span className="three-state-switch__label" id={switchId}>
        {name}
      </span>
      <div aria-labelledby={switchId} className={switchClassNames}>
        <button
          className={trueBtnClassNames}
          onClick={() => handleBtnClick(true)}
        >
          true
        </button>
        <button
          className={falseBtnClassNames}
          onClick={() => handleBtnClick(false)}
        >
          false
        </button>
        <button
          className={nullBtnClassNames}
          onClick={() => handleBtnClick(null)}
        >
          null
        </button>
      </div>
    </div>
  );
};

export default ThreeStateSwitch;
