// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
  useControlPlanePolling,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions } from "@xyflow/react";
import { useCallback } from "react";

import {
  useGetServicesDataQuery,
  useLazyGetServicesDataQuery,
} from "@/features/admin-panel/control-plane/api";
import {
  docSumGraphEdgesSelector,
  docSumGraphIsAutorefreshEnabledSelector,
  docSumGraphIsLoadingSelector,
  docSumGraphIsRenderableSelector,
  docSumGraphNodesSelector,
  setDocSumGraphIsAutorefreshEnabled,
} from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const dispatch = useAppDispatch();
  const isLoading = useAppSelector(docSumGraphIsLoadingSelector);
  const isRenderable = useAppSelector(docSumGraphIsRenderableSelector);
  const isAutorefreshEnabled = useAppSelector(
    docSumGraphIsAutorefreshEnabledSelector,
  );

  const [getServicesData, { isFetching }] = useLazyGetServicesDataQuery();

  const handleAutorefreshChange = useCallback(
    (enabled: boolean) => {
      dispatch(setDocSumGraphIsAutorefreshEnabled(enabled));
    },
    [dispatch],
  );

  const handleRefresh = useCallback(() => {
    getServicesData();
  }, [getServicesData]);

  useControlPlanePolling(handleRefresh, isAutorefreshEnabled);

  return (
    <ControlPlanePanel
      isLoading={isLoading}
      isRenderable={isRenderable}
      Graph={DocSumGraph}
      isAutorefreshEnabled={isAutorefreshEnabled}
      onAutorefreshChange={handleAutorefreshChange}
      onRefresh={handleRefresh}
      isFetching={isFetching}
    />
  );
};

const DocSumGraph = () => {
  const nodes = useAppSelector(docSumGraphNodesSelector);
  const edges = useAppSelector(docSumGraphEdgesSelector);

  const { colorScheme: colorMode } = useColorScheme();

  const fitViewOptions: FitViewOptions = {
    padding: 0.5,
    maxZoom: 1.5,
  };

  return (
    <PipelineGraph
      colorMode={colorMode}
      nodes={nodes}
      edges={edges}
      fitViewOptions={fitViewOptions}
    />
  );
};

export default ControlPlaneTab;
