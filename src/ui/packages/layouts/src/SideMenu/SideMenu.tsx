// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SideMenu.scss";

import { IconButton, Tooltip } from "@intel-enterprise-rag-ui/components";
import { IconName } from "@intel-enterprise-rag-ui/icons";
import classNames from "classnames";
import { PropsWithChildren, ReactNode } from "react";

type SideMenuDirection = "left" | "right";

interface SideMenuProps extends PropsWithChildren {
  /** Whether the side menu is open */
  isOpen: boolean;
  /** Accessible label for navigation */
  ariaLabel?: string;
  /** Content to display in the header */
  headerContent?: ReactNode;
  /** Direction of the side menu (left or right) */
  direction?: SideMenuDirection;
  /** Whether the side menu has a header */
  hasHeader?: boolean;
}

/**
 * Side navigation menu component for layout structure.
 * Supports left/right direction, header content, and open/close state.
 */
export const SideMenu = ({
  isOpen,
  ariaLabel,
  headerContent,
  direction = "right",
  hasHeader = false,
  children,
}: SideMenuProps) => (
  <nav
    className={classNames("side-menu", {
      "side-menu--open": isOpen,
      "side-menu--closed": !isOpen,
      "side-menu--left": direction === "left",
      "side-menu--right": direction === "right",
    })}
    role="navigation"
    aria-label={ariaLabel}
    aria-hidden={!isOpen}
  >
    {isOpen && (
      <>
        {hasHeader && (
          <header className="side-menu__header">{headerContent}</header>
        )}
        <div className="side-menu__content">{children}</div>
      </>
    )}
  </nav>
);
interface SideMenuIconButtonProps {
  isSideMenuOpen: boolean;
  sideMenuTitle?: string;
  onPress: () => void;
}

export const SideMenuIconButton = ({
  isSideMenuOpen,
  sideMenuTitle,
  onPress,
}: SideMenuIconButtonProps) => {
  const tooltipTitle = `${isSideMenuOpen ? "Close" : "Open"} ${sideMenuTitle || "Side Menu"}`;
  const icon: IconName = isSideMenuOpen ? "hide-side-menu" : "side-menu";
  const ariaLabel = `${isSideMenuOpen ? "Close" : "Open"} ${sideMenuTitle || "Side Menu"}`;

  return (
    <Tooltip
      title={tooltipTitle}
      trigger={
        <IconButton icon={icon} aria-label={ariaLabel} onPress={onPress} />
      }
      placement="bottom"
    />
  );
};
