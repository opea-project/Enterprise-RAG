// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./PageLayout.scss";

import { PropsWithChildren, ReactNode } from "react";

import AppHeader from "@/components/ui/AppHeader/AppHeader";

interface PageLayoutProps extends PropsWithChildren {
  appHeaderExtraActions?: ReactNode;
}

const PageLayout = ({ appHeaderExtraActions, children }: PageLayoutProps) => (
  <div className="page-layout__root">
    <div className="page-layout__content">
      <AppHeader extraActions={appHeaderExtraActions} />
      <main className="page-layout__main-outlet">{children}</main>
    </div>
  </div>
);

export default PageLayout;
