// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ThreeStateSwitch,
  ThreeStateSwitchProps,
  ThreeStateSwitchValue,
} from "@intel-enterprise-rag-ui/components";

type ServiceArgumentThreeStateSwitchProps = ThreeStateSwitchProps;

export type ServiceArgumentThreeStateSwitchValue = ThreeStateSwitchValue;

const ServiceArgumentThreeStateSwitch = (
  props: ServiceArgumentThreeStateSwitchProps,
) => <ThreeStateSwitch {...props} />;

export default ServiceArgumentThreeStateSwitch;
