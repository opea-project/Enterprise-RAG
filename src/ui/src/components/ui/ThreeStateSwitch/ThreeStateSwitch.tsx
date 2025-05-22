// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ThreeStateSwitch.scss";

import classNames from "classnames";
import { useEffect, useMemo, useState } from "react";
import { ToggleButton, ToggleButtonGroup } from "react-aria-components";
import { v4 as uuidv4 } from "uuid";

export type ThreeStateSwitchValue = boolean | null;

export interface ThreeStateSwitchProps {
  initialValue?: ThreeStateSwitchValue;
  name: string;
  readOnly?: boolean;
  onChange?: (name: string, value: boolean | null) => void;
}

const ThreeStateSwitch = ({
  initialValue = null,
  name,
  readOnly,
  onChange,
}: ThreeStateSwitchProps) => {
  const [state, setState] = useState<ThreeStateSwitchValue>(initialValue);

  useEffect(() => {
    if (readOnly) {
      setState(initialValue);
    }
  }, [readOnly, initialValue]);

  const handleBtnPress = (newValue: ThreeStateSwitchValue) => {
    if (!readOnly) {
      setState(newValue);

      if (onChange) {
        onChange(name, newValue);
      }
    }
  };

  const trueBtnClassNames = classNames("three-state-switch__button", {
    "three-state-switch__button--active": state === true,
  });

  const falseBtnClassNames = classNames("three-state-switch__button", {
    "three-state-switch__button--active": state === false,
  });

  const nullBtnClassNames = classNames("three-state-switch__button", {
    "three-state-switch__button--active": state === null,
  });

  const switchClassNames = classNames(
    {
      "three-state-switch--read-only": readOnly,
    },
    "three-state-switch",
  );

  const switchId = useMemo(
    () => `${name}-three-state-switch-${uuidv4()}`,
    [name],
  );

  return (
    <div>
      <label id={switchId} className="three-state-switch__label">
        {name}
      </label>
      <ToggleButtonGroup
        aria-labelledby={switchId}
        isDisabled={readOnly}
        className={switchClassNames}
      >
        <ToggleButton
          id="three-state-switch--true"
          className={trueBtnClassNames}
          onPress={() => handleBtnPress(true)}
        >
          true
        </ToggleButton>
        <ToggleButton
          id="three-state-switch--false"
          className={falseBtnClassNames}
          onPress={() => handleBtnPress(false)}
        >
          false
        </ToggleButton>
        <ToggleButton
          id="three-state-switch--null"
          className={nullBtnClassNames}
          onPress={() => handleBtnPress(null)}
        >
          null
        </ToggleButton>
      </ToggleButtonGroup>
    </div>
  );
};

export default ThreeStateSwitch;
