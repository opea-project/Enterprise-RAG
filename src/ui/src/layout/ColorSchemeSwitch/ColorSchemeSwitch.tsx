// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ColorSchemeSwitch.scss";

import classNames from "classnames";
import { PiMoonStarsFill, PiSunFill } from "react-icons/pi";

import useColorScheme from "@/utils/hooks/useColorScheme";

const ColorSchemeSwitch = () => {
  const { colorScheme, toggleColorScheme } = useColorScheme();

  const handleClick = () => {
    toggleColorScheme();
  };

  const getModeLabel = () => (colorScheme === "light" ? "Light" : "Dark");

  const getModeIcon = () =>
    colorScheme === "light" ? (
      <PiSunFill className="color-scheme-switch__thumb--icon" />
    ) : (
      <PiMoonStarsFill className="color-scheme-switch__thumb--icon" />
    );

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
