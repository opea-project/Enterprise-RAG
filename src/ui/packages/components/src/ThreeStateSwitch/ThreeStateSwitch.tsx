// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ThreeStateSwitch.scss";

import classNames from "classnames";
import { useEffect, useId, useMemo, useState } from "react";
import {
  ToggleButton as AriaToggleButton,
  ToggleButtonGroup as AriaToggleButtonGroup,
} from "react-aria-components";

export type ThreeStateSwitchValue = boolean | null;

export interface ThreeStateSwitchProps {
  /** Current value of the switch (true, false, or null) */
  value?: ThreeStateSwitchValue;
  /** Name of the switch input */
  name: string;
  /** If true, makes the switch read-only */
  isReadOnly?: boolean;
  /** Callback for value change */
  onChange?: (name: string, value: boolean | null) => void;
}

/**
 * Switch component supporting three states: true, false, and null.
 * Useful for tri-state toggles in forms.
 */
export const ThreeStateSwitch = ({
  value = null,
  name,
  isReadOnly,
  onChange,
}: ThreeStateSwitchProps) => {
  const id = useId();
  const switchId = useMemo(
    () => `${name}-three-state-switch-${id}`,
    [id, name],
  );

  const [state, setState] = useState<ThreeStateSwitchValue>(value);

  useEffect(() => {
    setState(value);
  }, [value]);

  const handleBtnPress = (newValue: ThreeStateSwitchValue) => {
    setState(newValue);

    if (onChange) {
      onChange(name, newValue);
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
      "three-state-switch--read-only": isReadOnly,
    },
    "three-state-switch",
  );

  return (
    <div>
      <label id={switchId} className="three-state-switch__label">
        {name}
      </label>
      <AriaToggleButtonGroup
        aria-labelledby={switchId}
        className={switchClassNames}
      >
        <AriaToggleButton
          id="three-state-switch--true"
          className={trueBtnClassNames}
          onPress={() => handleBtnPress(true)}
        >
          true
        </AriaToggleButton>
        <AriaToggleButton
          id="three-state-switch--false"
          className={falseBtnClassNames}
          onPress={() => handleBtnPress(false)}
        >
          false
        </AriaToggleButton>
        <AriaToggleButton
          id="three-state-switch--null"
          className={nullBtnClassNames}
          onPress={() => handleBtnPress(null)}
        >
          null
        </AriaToggleButton>
      </AriaToggleButtonGroup>
    </div>
  );
};
