// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconBaseProps } from "react-icons";
import { FaSpinner } from "react-icons/fa";

const LoadingIcon = ({ className, ...rest }: IconBaseProps) => (
  <FaSpinner {...rest} className={`${className} animate-spin`} />
);

export default LoadingIcon;
