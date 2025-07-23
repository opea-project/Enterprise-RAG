// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PageLayout.scss";

import classNames from "classnames";
import { PropsWithChildren, ReactNode } from "react";

import AppHeader, { AppHeaderProps } from "@/components/ui/AppHeader/AppHeader";

interface PageLayoutProps extends PropsWithChildren {
  appHeaderProps?: AppHeaderProps;
  leftSideMenu?: {
    component?: ReactNode;
    isOpen?: boolean;
  };
  rightSideMenu?: {
    component?: ReactNode;
    isOpen?: boolean;
  };
}

const PageLayout = ({
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

export default PageLayout;
