// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren } from "react";
import { Provider } from "react-redux";

import Notifications from "@/components/ui/Notifications/Notifications";
import { store } from "@/store";

const AppProvider = ({ children }: PropsWithChildren) => (
  <Provider store={store}>
    {children}
    <Notifications />
  </Provider>
);

export default AppProvider;
