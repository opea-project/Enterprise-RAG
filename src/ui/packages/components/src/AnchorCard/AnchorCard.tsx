// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./AnchorCard.scss";

import {
  ExternalLinkIcon,
  IconName,
  icons,
} from "@intel-enterprise-rag-ui/icons";
import { isSafeHref, sanitizeHref } from "@intel-enterprise-rag-ui/utils";
import classNames from "classnames";
import {
  Link as AriaLink,
  LinkProps as AriaLinkProps,
  PressEvent as AriaPressEvent,
} from "react-aria-components";

interface AnchorCardProps extends AriaLinkProps {
  /** Text to display in the anchor card */
  text: string;
  /** Name of the icon to display */
  icon?: IconName;
  /** If true, additional icon for indicating external links is displayed */
  isExternal?: boolean;
}

/**
 * Anchor component for rendering a styled link in the form of the card with optional icon and external indication.
 */
export const AnchorCard = ({
  text,
  icon,
  isExternal,
  href,
  target = "_blank",
  className,
  onPress,
  ...rest
}: AnchorCardProps) => {
  const isSafe = isSafeHref(href);
  const safeHref = isSafe ? sanitizeHref(href) : undefined;
  const rel = target === "_blank" ? "noopener noreferrer" : undefined;
  const anchorCardClassNames = classNames([
    "anchor-card",
    { invalid: !isSafe },
    className,
  ]);

  const handlePress = (event: AriaPressEvent) => {
    if (onPress && isSafe) {
      onPress(event);
    }
  };

  const IconComponent = icon ? icons[icon] : null;

  return (
    <AriaLink
      {...rest}
      href={safeHref}
      target={target}
      rel={rel}
      className={anchorCardClassNames}
      aria-disabled={!isSafe}
      onPress={handlePress}
    >
      <span className="anchor-card__content">
        {IconComponent ? <IconComponent /> : null}
        <p className="anchor-card__text">
          {!isSafe && "Caution: Malicious link - "}
          {text}
        </p>
        {isExternal && <ExternalLinkIcon fontSize={12} />}
      </span>
    </AriaLink>
  );
};
