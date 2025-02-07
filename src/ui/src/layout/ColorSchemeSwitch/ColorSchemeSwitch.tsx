// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ColorSchemeSwitch.scss";

import classNames from "classnames";

import DarkModeIcon from "@/components/icons/DarkModeIcon/DarkModeIcon";
import LightModeIcon from "@/components/icons/LightModeIcon/LightModeIcon";
import useColorScheme from "@/utils/hooks/useColorScheme";

const ColorSchemeSwitch = () => {
  const { colorScheme, toggleColorScheme } = useColorScheme();

  const handleClick = () => {
    toggleColorScheme();
  };

  const getModeLabel = () => (colorScheme === "light" ? "Light" : "Dark");

  const getModeIcon = () =>
    colorScheme === "light" ? <LightModeIcon /> : <DarkModeIcon />;

  const colorSchemeSwitchClassNames = classNames(
    "color-scheme-switch",
    colorScheme,
  );

  return (
    <button onClick={handleClick} className={colorSchemeSwitchClassNames}>
      <div className="color-scheme-switch__thumb">{getModeIcon()}</div>
      <p className="color-scheme-switch__label">{getModeLabel()}</p>
    </button>
  );
};

export default ColorSchemeSwitch;
