// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
import "./Anchor.scss";

import classNames from "classnames";
import { AnchorHTMLAttributes, MouseEventHandler } from "react";

import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { getPunycodeHref, isHrefSafe } from "@/utils";

interface AnchorProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  isExternal?: boolean;
}

const Anchor = ({
  href,
  target = "_blank",
  className,
  children,
  isExternal,
  ...props
}: AnchorProps) => {
  const linkClassNames = classNames({ className, invalid: !isHrefSafe(href) });
  const safeHref = isHrefSafe(href) ? getPunycodeHref(href) : undefined;

  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    if (!isHrefSafe(href)) {
      event.preventDefault();
    }
  };

  return (
    <a
      {...props}
      href={safeHref}
      target={target}
      className={linkClassNames}
      onClick={handleClick}
    >
      {!isHrefSafe && "Caution: Malicious link - "}
      {children}
      {isExternal && <ExternalLinkIcon size={12} />}
    </a>
  );
};

export default Anchor;
