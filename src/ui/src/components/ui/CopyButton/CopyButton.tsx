// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./CopyButton.scss";

import classNames from "classnames";
import { useState } from "react";

import { IconName } from "@/components/icons";
import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

interface CopyButtonProps {
  textToCopy: string;
  show?: boolean;
  forCodeSnippet?: boolean;
}

type CopyButtonState = "idle" | "success" | "error";

const CopyButton = ({
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
  const icon: IconName = copyState === "idle" ? "copy" : `copy-${copyState}`;

  const className = classNames("copy-btn", {
    "copy-btn--code-snippet": forCodeSnippet,
  });

  return (
    <Tooltip
      title="Copy"
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

export default CopyButton;
