// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
  ServiceData,
  useControlPlanePolling,
} from "@intel-enterprise-rag-ui/control-plane";
import { Node, NodeChange } from "@xyflow/react";
import { useCallback, useMemo } from "react";

import {
  useChangeArgumentsMutation,
  useGetServicesDataQuery,
  useLazyGetServicesDataQuery,
} from "@/features/admin-panel/control-plane/api";
import ServiceCard from "@/features/admin-panel/control-plane/components/ServiceCard/ServiceCard";
import {
  audioQnAGraphEdgesSelector,
  audioQnAGraphIsAutorefreshEnabledSelector,
  audioQnAGraphIsLoadingSelector,
  audioQnAGraphIsRenderableSelector,
  audioQnAGraphNodesSelector,
  onAudioQnAGraphConnect,
  onAudioQnAGraphEdgesChange,
  onAudioQnAGraphNodesChange,
  setAudioQnAGraphIsAutorefreshEnabled,
  setAudioQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/audioQnAGraph.slice";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const dispatch = useAppDispatch();
  const isLoading = useAppSelector(audioQnAGraphIsLoadingSelector);
  const isRenderable = useAppSelector(audioQnAGraphIsRenderableSelector);
  const isAutorefreshEnabled = useAppSelector(
    audioQnAGraphIsAutorefreshEnabledSelector,
  );

  const [getServicesData, { isFetching }] = useLazyGetServicesDataQuery();
  const [changeArguments] = useChangeArgumentsMutation();

  const handleAutorefreshChange = useCallback(
    (enabled: boolean) => {
      dispatch(setAudioQnAGraphIsAutorefreshEnabled(enabled));
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
      Graph={AudioQnAGraph}
      ConfigPanel={() => <ServiceCard changeArguments={changeArguments} />}
      isAutorefreshEnabled={isAutorefreshEnabled}
      onAutorefreshChange={handleAutorefreshChange}
      onRefresh={handleRefresh}
      isFetching={isFetching}
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

  const fitViewOptions = useMemo(
    () => ({
      padding: {
        x: 0.75,
        y: 0.5,
      },
    }),
    [],
  );

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
