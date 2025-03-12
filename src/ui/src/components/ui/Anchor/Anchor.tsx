// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./Anchor.scss";

import classNames from "classnames";
import { AnchorHTMLAttributes, MouseEventHandler } from "react";

import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { isSafeHref, sanitizeHref } from "@/utils";

interface AnchorProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  isExternal?: boolean;
}

const Anchor = ({
  href,
  target = "_blank",
  className,
  children,
  isExternal,
  onClick,
  ...attrs
}: AnchorProps) => {
  const isSafe = isSafeHref(href);
  const safeHref = isSafe ? sanitizeHref(href) : undefined;
  const rel = target === "_blank" ? "noopener noreferrer" : undefined;
  const anchorClassNames = classNames([{ invalid: !isSafe }, className]);

  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    if (!isSafe) {
      event.preventDefault();
    } else if (onClick) {
      onClick(event);
    }
  };

  return (
    <a
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorClassNames}
      onClick={handleClick}
      {...attrs}
    >
      {!isSafe && "Caution: Malicious link - "}
      {children}
      {isExternal && <ExternalLinkIcon size={12} />}
    </a>
  );
};

export default Anchor;
