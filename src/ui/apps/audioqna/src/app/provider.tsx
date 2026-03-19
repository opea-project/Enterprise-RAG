// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Notifications } from "@intel-enterprise-rag-ui/components";
import { PropsWithChildren } from "react";
import { Provider } from "react-redux";

import { store } from "@/store";

const AppProvider = ({ children }: PropsWithChildren) => (
  <Provider store={store}>
    {children}
    <Notifications />
  </Provider>
);

export default AppProvider;
