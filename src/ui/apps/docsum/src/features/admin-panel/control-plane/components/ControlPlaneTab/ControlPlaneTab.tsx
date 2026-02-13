// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions } from "@xyflow/react";

import { useGetServicesDataQuery } from "@/features/admin-panel/control-plane/api";
import {
  docSumGraphEdgesSelector,
  docSumGraphIsLoadingSelector,
  docSumGraphIsRenderableSelector,
  docSumGraphNodesSelector,
} from "@/features/admin-panel/control-plane/store/docSumGraph.slice";
import { useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const isLoading = useAppSelector(docSumGraphIsLoadingSelector);
  const isRenderable = useAppSelector(docSumGraphIsRenderableSelector);

  return (
    <ControlPlanePanel
      isLoading={isLoading}
      isRenderable={isRenderable}
      Graph={DocSumGraph}
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
