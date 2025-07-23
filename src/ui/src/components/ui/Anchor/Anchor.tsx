// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Anchor.scss";

import classNames from "classnames";
import { ReactNode } from "react";
import { Link, LinkProps, PressEvent } from "react-aria-components";

import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { isSafeHref, sanitizeHref } from "@/utils";

export interface AnchorProps extends LinkProps {
  children: ReactNode;
  isExternal?: boolean;
}

const Anchor = ({
  children,
  isExternal,
  href,
  target = "_blank",
  className,
  onPress,
  ...rest
}: AnchorProps) => {
  const isSafe = isSafeHref(href);
  const safeHref = isSafe ? sanitizeHref(href) : undefined;
  const rel = target === "_blank" ? "noopener noreferrer" : undefined;
  const anchorClassNames = classNames([{ invalid: !isSafe }, className]);

  const handlePress = (event: PressEvent) => {
    if (onPress && isSafe) {
      onPress(event);
    }
  };

  return (
    <Link
      {...rest}
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorClassNames}
      onPress={handlePress}
      aria-disabled={!isSafe}
    >
      {!isSafe && "Caution: Malicious link - "}
      {children}
      {isExternal && <ExternalLinkIcon size={12} />}
    </Link>
  );
};

export default Anchor;
