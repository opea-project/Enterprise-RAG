// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect } from "react";

import SystemFingerprintService from "@/services/systemFingerprintService";
import {
  setHasInputGuard,
  setHasOutputGuard,
} from "@/store/chatQnAGraph.slice";
import { useAppDispatch } from "@/store/hooks";

const useCheckChatPipelineConfig = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    SystemFingerprintService.getChatQnAServiceDetails()
      .then((details) => {
        if (details) {
          const hasInputGuard = details.input_guard.status !== undefined;
          const hasOutputGuard = details.output_guard.status !== undefined;
          dispatch(setHasInputGuard(hasInputGuard));
          dispatch(setHasOutputGuard(hasOutputGuard));
        }
      })
      .catch((error) => {
        console.error("Failed to fetch chatqa pipeline service details", error);
      });
  }, [dispatch]);
};

export default useCheckChatPipelineConfig;
