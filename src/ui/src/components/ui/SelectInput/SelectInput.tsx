// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SelectInput.scss";

import classNames from "classnames";
import { useId } from "react";
import {
  Button,
  Key,
  Label,
  ListBox,
  ListBoxItem,
  Popover,
  Select,
  SelectProps,
  SelectValue,
} from "react-aria-components";
import { BsCaretDownFill, BsCaretUpFill } from "react-icons/bs";

import InfoIcon from "@/components/icons/InfoIcon/InfoIcon";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

type SelectInputSize = "sm";
export type SelectInputChangeHandler<T = Key> = (item: T) => void;

interface SelectInputProps<T = Key> extends SelectProps {
  value?: T | null;
  items?: string[];
  label?: string;
  size?: SelectInputSize;
  isDisabled?: boolean;
  isInvalid?: boolean;
  placeholder?: string;
  tooltipText?: string;
  fullWidth?: boolean;
  onChange?: SelectInputChangeHandler<T>;
}

const SelectInput = <T extends Key = Key>({
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
  ...restProps
}: SelectInputProps<T>) => {
  const inputId = useId();

  const selectOptions = items
    ? items.map((item, index) => (
        <ListBoxItem
          key={`${inputId}-${index}-list-item`}
          // id is value passed to onChange handler
          id={item}
          textValue={item}
          className="select-input__options-list-item"
        >
          {item}
        </ListBoxItem>
      ))
    : null;

  return (
    <Select
      isDisabled={isDisabled}
      isInvalid={isInvalid}
      selectedKey={value}
      onSelectionChange={onChange as (key: Key) => void}
      className={classNames(
        "select-input",
        {
          "select-input--sm": size === "sm",
        },
        className,
      )}
      {...restProps}
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
              <Label htmlFor={inputId} className="select-input__label">
                {label}
              </Label>
            </span>
          )}
          <Button
            className={classNames("select-input__button", {
              "w-full": fullWidth,
            })}
            slot="button"
            aria-haspopup="listbox"
            aria-expanded={isOpen}
          >
            <SelectValue className="select-input__value">
              {({ selectedText }) =>
                selectedText || placeholder || "Select value from the list"
              }
            </SelectValue>
            {isOpen ? <BsCaretUpFill /> : <BsCaretDownFill />}
          </Button>
          <Popover>
            <ListBox
              className={classNames("select-input__options-list", {
                "select-input__options-list--sm": size === "sm",
              })}
            >
              {selectOptions}
            </ListBox>
          </Popover>
        </>
      )}
    </Select>
  );
};

export default SelectInput;
