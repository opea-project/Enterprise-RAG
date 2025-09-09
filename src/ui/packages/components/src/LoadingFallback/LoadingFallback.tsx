// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./LoadingFallback.scss";

import { LoadingIcon } from "@intel-enterprise-rag-ui/icons";

interface LoadingFallbackProps {
  /** Message to display while loading */
  loadingMessage?: string;
}

/**
 * Loading fallback component for displaying a loading indicator and message.
 */
export const LoadingFallback = ({ loadingMessage }: LoadingFallbackProps) => (
  <div className="loading-fallback">
    <div className="loading-fallback__content">
      <LoadingIcon className="loading-fallback__icon" />
      <p className="loading-fallback__message">
        {loadingMessage ?? "Loading..."}
      </p>
    </div>
  </div>
);
