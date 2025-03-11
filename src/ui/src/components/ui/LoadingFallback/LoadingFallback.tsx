// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import LoadingIcon from "@/components/icons/LoadingIcon/LoadingIcon";

const LoadingFallback = () => (
  <div className="flex h-full w-full items-center justify-center">
    <div className="flex items-center gap-3">
      <LoadingIcon />
      <p className="mb-0">Loading...</p>
    </div>
  </div>
);

export default LoadingFallback;
