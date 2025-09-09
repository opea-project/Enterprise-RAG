// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useSearchParams } from "react-router-dom";

const useDebug = () => {
  const [searchParams] = useSearchParams();
  const isDebugEnabled = searchParams.get("debug") === "true";

  return { isDebugEnabled };
};

export default useDebug;
