// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
import "./Anchor.scss";

import classNames from "classnames";
import { toASCII } from "punycode";
import { AnchorHTMLAttributes, MouseEventHandler } from "react";
import { BsBoxArrowUpRight } from "react-icons/bs";

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
  const getPunycodeHref = () => {
    if (!href) {
      return href;
    }

    const decodedHref = decodeURIComponent(href);
    return toASCII(decodedHref);
  };
  const isHrefSafe = getPunycodeHref() === href;
  const linkClassNames = classNames({ className, invalid: !isHrefSafe });
  const safeHref = isHrefSafe ? getPunycodeHref() : undefined;

  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    if (!isHrefSafe) {
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
      {isExternal && <BsBoxArrowUpRight size={12} />}
    </a>
  );
};

export default Anchor;
