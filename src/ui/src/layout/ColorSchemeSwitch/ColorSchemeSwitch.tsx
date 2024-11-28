// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ColorSchemeSwitch.scss";

import { Icon } from "@iconify/react";
import classNames from "classnames";

import useColorScheme from "@/utils/hooks/useColorScheme";

const ColorSchemeSwitch = () => {
  const { colorScheme, toggleColorScheme } = useColorScheme();

  const handleClick = () => {
    toggleColorScheme();
  };

  const getModeLabel = () => (colorScheme === "light" ? "Light" : "Dark");

  const getModeIcon = () =>
    colorScheme === "light" ? "solar:sun-bold" : "solar:moon-stars-bold";

  const colorSchemeSwitchClassNames = classNames(
    "color-scheme-switch",
    colorScheme,
  );

  return (
    <button onClick={handleClick} className={colorSchemeSwitchClassNames}>
      <div className="color-scheme-switch__thumb">
        <Icon
          icon={getModeIcon()}
          className="color-scheme-switch__thumb--icon"
        />
      </div>
      <p className="color-scheme-switch__label">{getModeLabel()}</p>
    </button>
  );
};

export default ColorSchemeSwitch;
