// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./ColorSchemeSwitch.scss";

import { DarkModeIcon, LightModeIcon } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";

import { Button } from "@/Button/Button";
import { useColorScheme } from "@/ColorSchemeSwitch/useColorScheme";

/**
 * Color scheme switch component for toggling between light and dark modes.
 */
export const ColorSchemeSwitch = () => {
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
    <Button className={colorSchemeSwitchClassNames} onPress={handleClick}>
      <div className="color-scheme-switch__thumb">{getModeIcon()}</div>
      <p className="color-scheme-switch__label">{getModeLabel()}</p>
    </Button>
  );
};
