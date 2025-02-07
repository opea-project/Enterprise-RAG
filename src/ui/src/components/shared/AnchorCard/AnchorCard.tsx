// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AnchorCard.scss";

import { AnchorHTMLAttributes, MouseEventHandler } from "react";

import { IconName, icons } from "@/components/icons";
import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { getPunycodeHref, isHrefSafe } from "@/utils";

interface AnchorCardProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
  text: string;
  icon?: IconName;
  isExternal?: boolean;
}

const AnchorCard = ({ text, href, icon, isExternal }: AnchorCardProps) => {
  const safeHref = isHrefSafe(href) ? getPunycodeHref(href) : undefined;

  const handleClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    if (!isHrefSafe(href)) {
      event.preventDefault();
    }
  };

  let content = (
    <>
      {text}
      {isExternal && <ExternalLinkIcon fontSize={12} />}
    </>
  );
  if (icon) {
    const IconComponent = icons[icon];
    content = (
      <>
        <IconComponent />
        {text}
        {isExternal && <ExternalLinkIcon fontSize={12} />}
      </>
    );
  }

  return (
    <a
      href={safeHref}
      target="_blank"
      className="anchor-card"
      onClick={handleClick}
    >
      <span className="anchor-card__content">{content}</span>
    </a>
  );
};

export default AnchorCard;
