// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { MouseEventHandler, useState } from "react";

import { IconName } from "@/components/icons";
import IconButton, {
  IconButtonColor,
} from "@/components/ui/IconButton/IconButton";

type CopyButtonState = "idle" | "success" | "error";

interface CopyButtonProps {
  rawCode: string;
}

const CopyButton = ({ rawCode }: CopyButtonProps) => {
  const [copyBtnState, setCopyBtnState] = useState<CopyButtonState>("idle");

  const handleCopyBtnClick: MouseEventHandler = () => {
    navigator.clipboard
      .writeText(rawCode)
      .then(() => {
        setCopyBtnState("success");
      })
      .catch((error) => {
        setCopyBtnState("error");
        console.error(error);
      })
      .finally(() => {
        setTimeout(() => {
          setCopyBtnState("idle");
        }, 1000);
      });
  };

  const icon: IconName =
    copyBtnState === "idle" ? "copy" : `copy-${copyBtnState}`;

  const color: IconButtonColor =
    copyBtnState === "idle" ? "primary" : copyBtnState;

  return (
    <IconButton
      icon={icon}
      color={color}
      size="sm"
      className="absolute right-4 top-4 bg-light-bg-contrast dark:bg-dark-bg-contrast"
      onClick={handleCopyBtnClick}
    />
  );
};

export default CopyButton;
