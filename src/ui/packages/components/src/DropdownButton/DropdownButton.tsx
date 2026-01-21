// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DropdownButton.scss";

import { SelectInputArrowDown } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { Button as AriaButton, Selection } from "react-aria-components";

import { Menu, MenuItem, MenuTrigger } from "@/Menu/Menu";

export interface DropdownButtonOption {
  value: string;
  label: string;
}

export interface DropdownButtonProps {
  /** Primary button label */
  label: string;
  /** Current selected option value */
  selectedValue: string;
  /** Available options for dropdown */
  options: DropdownButtonOption[];
  /** Callback when primary button is pressed */
  onPress: () => void;
  /** Callback when an option is selected */
  onSelectionChange: (value: string) => void;
  /** Whether the button is disabled */
  isDisabled?: boolean;
  /** Aria label for the dropdown trigger button */
  ariaLabel?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * DropdownButton component combining a primary action button with a dropdown menu for options.
 */
export const DropdownButton = ({
  label,
  selectedValue,
  options,
  onPress,
  onSelectionChange,
  isDisabled = false,
  ariaLabel = "Change selection",
  className,
}: DropdownButtonProps) => {
  const selectedOption = options.find((opt) => opt.value === selectedValue);
  const buttonLabel = selectedOption
    ? `${label} (${selectedOption.label})`
    : label;

  const handleSelectionChange = (keys: Selection) => {
    const key = Array.from(keys)[0] as string;
    if (key) {
      onSelectionChange(key);
    }
  };

  return (
    <div className={classNames("dropdown-button", className)}>
      <AriaButton
        className="dropdown-button__main"
        onPress={onPress}
        isDisabled={isDisabled}
      >
        {buttonLabel}
      </AriaButton>
      <MenuTrigger
        placement="bottom end"
        ariaLabel={ariaLabel}
        trigger={
          <AriaButton
            className="dropdown-button__trigger"
            isDisabled={isDisabled}
            aria-label={ariaLabel}
          >
            <SelectInputArrowDown fontSize={12} />
          </AriaButton>
        }
      >
        <Menu
          selectionMode="single"
          selectedKeys={[selectedValue]}
          onSelectionChange={handleSelectionChange}
        >
          {options.map((option) => (
            <MenuItem key={option.value} id={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Menu>
      </MenuTrigger>
    </div>
  );
};
