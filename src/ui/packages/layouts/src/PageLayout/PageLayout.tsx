// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PageLayout.scss";

import classNames from "classnames";
import { PropsWithChildren, ReactNode } from "react";

import { AppHeader, AppHeaderProps } from "@/AppHeader/AppHeader";

interface PageLayoutProps extends PropsWithChildren {
  /** Props for the application header */
  appHeaderProps?: AppHeaderProps;
  /** Configuration for the left side menu */
  leftSideMenu?: {
    /** Component to render in the left side menu */
    component?: ReactNode;
    /** Whether the left side menu is open */
    isOpen?: boolean;
  };
  /** Configuration for the right side menu */
  rightSideMenu?: {
    /** Component to render in the right side menu */
    component?: ReactNode;
    /** Whether the right side menu is open */
    isOpen?: boolean;
  };
}

/**
 * Page layout component for structuring application pages.
 * Supports header, left/right side menus, and main content area.
 */
export const PageLayout = ({
  appHeaderProps,
  leftSideMenu,
  rightSideMenu,
  children,
}: PageLayoutProps) => {
  const { component: LeftSideMenu, isOpen: isLeftSideMenuOpen } =
    leftSideMenu ?? {};
  const { component: RightSideMenu, isOpen: isRightSideMenuOpen } =
    rightSideMenu ?? {};

  return (
    <div className="page-layout__root">
      <div
        className={classNames("page-layout__content", {
          "page-layout__content--left-side-menu-open": isLeftSideMenuOpen,
          "page-layout__content--right-side-menu-open": isRightSideMenuOpen,
        })}
      >
        <AppHeader {...appHeaderProps} />
        <main className="page-layout__main-outlet" id="main">
          {children}
        </main>
      </div>
      {isLeftSideMenuOpen && LeftSideMenu}
      {isRightSideMenuOpen && RightSideMenu}
    </div>
  );
};
