// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SelectInput.scss";

import {
  InfoIcon,
  SelectInputArrowDown,
  SelectInputArrowUp,
} from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useId } from "react";
import {
  Button as AriaButton,
  Key as AriaKey,
  ListBox as AriaListBox,
  ListBoxItem as AriaListBoxItem,
  Popover as AriaPopover,
  Select as AriaSelect,
  SelectProps as AriaSelectProps,
  SelectValue as AriaSelectValue,
} from "react-aria-components";

import { Label } from "@/Label/Label";
import { Tooltip } from "@/Tooltip/Tooltip";

type SelectInputSize = "sm";
export type SelectInputChangeHandler<T = AriaKey> = (item: T) => void;

interface SelectInputProps<T = AriaKey> extends AriaSelectProps {
  /** Selected value */
  value?: T | null;
  /** List of selectable items */
  items?: string[];
  /** Label for the select input */
  label?: string;
  /** Size of the select input */
  size?: SelectInputSize;
  /** If true, disables the select input */
  isDisabled?: boolean;
  /** If true, marks the input as invalid */
  isInvalid?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Tooltip text for additional info */
  tooltipText?: string;
  /** If true, select input takes full width */
  fullWidth?: boolean;
  /** Callback for value change */
  onChange?: SelectInputChangeHandler<T>;
}

/**
 * Select input component for choosing from a list of options, with label, validation, and tooltip support.
 */
export const SelectInput = <T extends AriaKey = AriaKey>({
  items,
  label,
  size,
  isDisabled,
  isInvalid,
  placeholder,
  tooltipText,
  fullWidth,
  className,
  value,
  onChange,
  ...rest
}: SelectInputProps<T>) => {
  const inputId = useId();

  const selectOptions = items
    ? items.map((item, index) => (
        <AriaListBoxItem
          key={`${inputId}-${index}-list-item`}
          // id is value passed to onChange handler
          id={item}
          textValue={item}
          className="select-input__options-list-item"
        >
          {item}
        </AriaListBoxItem>
      ))
    : null;

  return (
    <AriaSelect
      isDisabled={isDisabled}
      isInvalid={isInvalid}
      selectedKey={value}
      className={classNames(
        "select-input",
        {
          "select-input--sm": size === "sm",
        },
        className,
      )}
      onSelectionChange={onChange as (key: AriaKey | null) => void}
      {...rest}
    >
      {({ isOpen }) => (
        <>
          {label && (
            <span className="select-input__label-wrapper">
              {tooltipText && (
                <Tooltip
                  title={tooltipText}
                  trigger={<InfoIcon aria-hidden="true" />}
                  placement="left"
                />
              )}
              <Label htmlFor={inputId} size={size}>
                {label}
              </Label>
            </span>
          )}
          <AriaButton
            className={classNames("select-input__button", {
              "w-full": fullWidth,
            })}
            slot="button"
            aria-haspopup="listbox"
            aria-expanded={isOpen}
          >
            <AriaSelectValue className="select-input__value">
              {({ selectedText }) =>
                selectedText || placeholder || "Select value from the list"
              }
            </AriaSelectValue>
            {isOpen ? <SelectInputArrowUp /> : <SelectInputArrowDown />}
          </AriaButton>
          <AriaPopover>
            <AriaListBox
              className={classNames("select-input__options-list", {
                "select-input__options-list--sm": size === "sm",
              })}
            >
              {selectOptions}
            </AriaListBox>
          </AriaPopover>
        </>
      )}
    </AriaSelect>
  );
};
