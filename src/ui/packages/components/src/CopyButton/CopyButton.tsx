// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./CopyButton.scss";

import { IconName } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { useState } from "react";

import { IconButton } from "@/IconButton/IconButton";
import { Tooltip } from "@/Tooltip/Tooltip";

type CopyButtonState = "idle" | "success" | "error";

interface CopyButtonProps {
  /** Text to copy to clipboard */
  textToCopy: string;
  /** If true, shows the copy button */
  show?: boolean;
  /** If true, styles for code snippet context */
  forCodeSnippet?: boolean;
}

/**
 * Copy button component for copying text to clipboard, with feedback and optional code snippet styling.
 */
export const CopyButton = ({
  textToCopy,
  show = true,
  forCodeSnippet = false,
}: CopyButtonProps) => {
  const [copyState, setCopyState] = useState<CopyButtonState>("idle");

  // Clipboard API is only available in secure contexts (HTTPS)
  if (!window.isSecureContext || !show) {
    return null;
  }

  const handlePress = () => {
    if (copyState !== "idle") {
      return;
    }

    navigator.clipboard
      .writeText(textToCopy)
      .then(() => {
        setCopyState("success");
      })
      .catch((error) => {
        setCopyState("error");
        console.error(error);
      })
      .finally(() => {
        setTimeout(() => {
          setCopyState("idle");
        }, 1000);
      });
  };

  const tooltipPlacement = forCodeSnippet ? "right" : "bottom";
  const tooltipText =
    copyState === "idle"
      ? "Copy"
      : copyState === "success"
        ? "Copied!"
        : "Error";
  const icon: IconName = copyState === "idle" ? "copy" : `copy-${copyState}`;

  const className = classNames("copy-btn", {
    "copy-btn--code-snippet": forCodeSnippet,
  });

  return (
    <Tooltip
      title={tooltipText}
      placement={tooltipPlacement}
      aria-label="Copy"
      trigger={
        <IconButton
          icon={icon}
          size="sm"
          className={className}
          onPress={handlePress}
        />
      }
    />
  );
};
