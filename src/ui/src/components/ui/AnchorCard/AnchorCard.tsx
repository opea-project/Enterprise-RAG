// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AnchorCard.scss";

import classNames from "classnames";
import { AnchorHTMLAttributes, MouseEventHandler } from "react";

import { IconName, icons } from "@/components/icons";
import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { isSafeHref, sanitizeHref } from "@/utils";

interface AnchorCardProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  text: string;
  icon?: IconName;
  isExternal?: boolean;
}

const AnchorCard = ({
  text,
  icon,
  isExternal,
  href,
  target = "_blank",
  className,
  onClick,
  ...attrs
}: AnchorCardProps) => {
  const isSafe = isSafeHref(href);
  const safeHref = isSafe ? sanitizeHref(href) : undefined;
  const rel = target === "_blank" ? "noopener noreferrer" : undefined;
  const anchorCardClassNames = classNames([
    "anchor-card",
    { invalid: !isSafe },
    className,
  ]);

  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    if (!isSafe) {
      event.preventDefault();
    } else if (onClick) {
      onClick(event);
    }
  };

  const IconComponent = icon ? icons[icon] : null;

  return (
    <a
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorCardClassNames}
      onClick={handleClick}
      {...attrs}
    >
      <span className="anchor-card__content">
        {IconComponent ? <IconComponent /> : null}
        <p className="anchor-card__text">
          {!isSafe && "Caution: Malicious link - "}
          {text}
        </p>
        {isExternal && <ExternalLinkIcon fontSize={12} />}
      </span>
    </a>
  );
};

export default AnchorCard;
