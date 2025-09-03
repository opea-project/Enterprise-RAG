// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ThreeStateSwitch, {
  ThreeStateSwitchProps,
  ThreeStateSwitchValue,
} from "@/components/ui/ThreeStateSwitch/ThreeStateSwitch";

type ServiceArgumentThreeStateSwitchProps = ThreeStateSwitchProps;

export type ServiceArgumentThreeStateSwitchValue = ThreeStateSwitchValue;

const ServiceArgumentThreeStateSwitch = (
  props: ServiceArgumentThreeStateSwitchProps,
) => {
  return <ThreeStateSwitch {...props} />;
};

export default ServiceArgumentThreeStateSwitch;
