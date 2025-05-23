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
}

type CopyButtonState = "idle" | "success" | "error";

const CopyButton = ({ textToCopy, show = true }: CopyButtonProps) => {
  const [copyState, setCopyState] = useState<CopyButtonState>("idle");

  // Clipboard API is only available in secure contexts (HTTPS)
  if (!window.isSecureContext) {
    return null;
  }

  const handlePress = () => {
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

  const icon: IconName = copyState === "idle" ? "copy" : `copy-${copyState}`;

  const className = classNames("copy-btn", {
    visible: show,
    invisible: !show,
  });

  return (
    <Tooltip
      title="Copy"
      placement="bottom"
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
