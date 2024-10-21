// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ThreeStateSwitch.scss";

import classNames from "classnames";
import { useState } from "react";

interface ThreeStateSwitchProps {
  initialValue?: boolean | null;
  onChange?: (value: boolean | null) => void;
}

const ThreeStateSwitch = ({
  initialValue = null,
  onChange,
}: ThreeStateSwitchProps) => {
  const [state, setState] = useState(initialValue);

  const handleBtnClick = (value: boolean | null) => {
    setState(value);
    if (onChange) {
      onChange(value);
    }
  };

  const trueBtnClassNames = classNames({
    "three-state-switch--button": true,
    "three-state-switch--button__active": state === true,
  });

  const falseBtnClassNames = classNames({
    "three-state-switch--button": true,
    "three-state-switch--button__active": state === false,
  });

  const nullBtnClassNames = classNames({
    "three-state-switch--button": true,
    "three-state-switch--button__active": state === null,
  });

  return (
    <div className="three-state-switch">
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
  );
};

export default ThreeStateSwitch;
