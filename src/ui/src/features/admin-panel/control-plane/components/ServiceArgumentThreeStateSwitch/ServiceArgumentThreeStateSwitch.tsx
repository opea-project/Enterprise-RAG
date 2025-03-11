// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ThreeStateSwitch, {
  ThreeStateSwitchProps,
  ThreeStateSwitchValue,
} from "@/components/ui/ThreeStateSwitch/ThreeStateSwitch";
import { chatQnAGraphEditModeEnabledSelector } from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { useAppSelector } from "@/store/hooks";

type ServiceArgumentThreeStateSwitchProps = ThreeStateSwitchProps;

export type ServiceArgumentThreeStateSwitchValue = ThreeStateSwitchValue;

const ServiceArgumentThreeStateSwitch = (
  props: ServiceArgumentThreeStateSwitchProps,
) => {
  const isEditModeEnabled = useAppSelector(chatQnAGraphEditModeEnabledSelector);
  const readOnly = !isEditModeEnabled;

  return <ThreeStateSwitch {...props} readOnly={readOnly} />;
};

export default ServiceArgumentThreeStateSwitch;
