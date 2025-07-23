// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./SideMenu.scss";

import classNames from "classnames";
import { PropsWithChildren, ReactNode } from "react";

import IconButton from "@/components/ui/IconButton/IconButton";
import Tooltip from "@/components/ui/Tooltip/Tooltip";

type SideMenuDirection = "left" | "right";

interface SideMenuProps extends PropsWithChildren {
  isOpen: boolean;
  ariaLabel?: string;
  headerContent?: ReactNode;
  direction?: SideMenuDirection;
}

const SideMenu = ({
  isOpen,
  ariaLabel,
  headerContent,
  direction = "right",
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
        <header className="side-menu__header">{headerContent}</header>
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
  const icon = isSideMenuOpen ? "hide-side-menu" : "side-menu";
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

export default SideMenu;
