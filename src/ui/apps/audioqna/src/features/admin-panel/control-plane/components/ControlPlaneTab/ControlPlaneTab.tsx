// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions, Node, NodeChange } from "@xyflow/react";
import { useCallback } from "react";

import { useGetServicesDataQuery } from "@/features/admin-panel/control-plane/api";
import {
  audioQnAGraphEdgesSelector,
  audioQnAGraphIsLoadingSelector,
  audioQnAGraphIsRenderableSelector,
  audioQnAGraphNodesSelector,
  onAudioQnAGraphConnect,
  onAudioQnAGraphEdgesChange,
  onAudioQnAGraphNodesChange,
  setAudioQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/audioQnAGraph.slice";
import { ServiceData } from "@/features/admin-panel/control-plane/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const isLoading = useAppSelector(audioQnAGraphIsLoadingSelector);
  const isRenderable = useAppSelector(audioQnAGraphIsRenderableSelector);

  return (
    <ControlPlanePanel
      isLoading={isLoading}
      isRenderable={isRenderable}
      Graph={AudioQnAGraph}
    />
  );
};

const AudioQnAGraph = () => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(audioQnAGraphNodesSelector);
  const edges = useAppSelector(audioQnAGraphEdgesSelector);

  const { colorScheme: colorMode } = useColorScheme();

  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node<Record<string, unknown>>[] }) => {
      dispatch(
        setAudioQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (
    changes: NodeChange<Node<Record<string, unknown>>>[],
  ) => {
    dispatch(
      onAudioQnAGraphNodesChange(changes as NodeChange<Node<ServiceData>>[]),
    );
  };

  const fitViewOptions: FitViewOptions = {
    padding: { x: 0.75 },
  };

  return (
    <PipelineGraph
      nodes={nodes}
      edges={edges}
      fitViewOptions={fitViewOptions}
      onNodesChange={handleNodesChange}
      onEdgesChange={onAudioQnAGraphEdgesChange}
      onSelectionChange={handleSelectionChange}
      onConnect={onAudioQnAGraphConnect}
      colorMode={colorMode}
    />
  );
};

export default ControlPlaneTab;
