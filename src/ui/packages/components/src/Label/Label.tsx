// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Label.scss";

import classNames from "classnames";
import { PropsWithChildren } from "react";
import {
  Label as AriaLabel,
  LabelProps as AriaLabelProps,
} from "react-aria-components";

type LabelSize = "sm" | "md";

interface LabelProps extends AriaLabelProps, PropsWithChildren {
  /** Size of the label (small or medium) */
  size?: LabelSize;
}

/**
 * Label component for form fields and UI elements.
 */
export const Label = ({ htmlFor, size = "md", children }: LabelProps) => (
  <AriaLabel
    htmlFor={htmlFor}
    className={classNames("label", {
      "label--sm": size === "sm",
    })}
  >
    {children}
  </AriaLabel>
);
