// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Anchor.scss";

import { ExternalLinkIcon } from "@intel-enterprise-rag-ui/icons";
import { isSafeHref, sanitizeHref } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import { ReactNode } from "react";
import {
  Link as AriaLink,
  LinkProps as AriaLinkProps,
  PressEvent as AriaPressEvent,
} from "react-aria-components";

export interface AnchorProps extends AriaLinkProps {
  /** Content to display inside the anchor */
  children: ReactNode;
  /** If true, additional icon for indicating external links is displayed */
  isExternal?: boolean;
}

/**
 * Anchor component for rendering a styled link with external indication and safe href handling.
 */
export const Anchor = ({
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

  const handlePress = (event: AriaPressEvent) => {
    if (onPress && isSafe) {
      onPress(event);
    }
  };

  return (
    <AriaLink
      {...rest}
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorClassNames}
      aria-disabled={!isSafe}
      onPress={handlePress}
    >
      {!isSafe && "Caution: Malicious link - "}
      {children}
      {isExternal && <ExternalLinkIcon size={12} />}
    </AriaLink>
  );
};
