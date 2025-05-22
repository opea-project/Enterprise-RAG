// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AnchorCard.scss";

import classNames from "classnames";
import { Link, LinkProps, PressEvent } from "react-aria-components";

import { IconName, icons } from "@/components/icons";
import ExternalLinkIcon from "@/components/icons/ExternalLinkIcon/ExternalLinkIcon";
import { isSafeHref, sanitizeHref } from "@/utils";

interface AnchorCardProps extends LinkProps {
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
  onPress,
  ...props
}: AnchorCardProps) => {
  const isSafe = isSafeHref(href);
  const safeHref = isSafe ? sanitizeHref(href) : undefined;
  const rel = target === "_blank" ? "noopener noreferrer" : undefined;
  const anchorCardClassNames = classNames([
    "anchor-card",
    { invalid: !isSafe },
    className,
  ]);

  const handlePress = (event: PressEvent) => {
    if (onPress && isSafe) {
      onPress(event);
    }
  };

  const IconComponent = icon ? icons[icon] : null;

  return (
    <Link
      {...props}
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorCardClassNames}
      onPress={handlePress}
      aria-disabled={!isSafe}
    >
      <span className="anchor-card__content">
        {IconComponent ? <IconComponent /> : null}
        <p className="anchor-card__text">
          {!isSafe && "Caution: Malicious link - "}
          {text}
        </p>
        {isExternal && <ExternalLinkIcon fontSize={12} />}
      </span>
    </Link>
  );
};

export default AnchorCard;
