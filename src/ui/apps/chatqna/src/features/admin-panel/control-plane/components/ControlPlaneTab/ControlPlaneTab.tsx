// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
  useControlPlanePolling,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions, Node, NodeChange } from "@xyflow/react";
import { useCallback, useMemo } from "react";

import {
  useGetServicesDataQuery,
  useLazyGetServicesDataQuery,
} from "@/features/admin-panel/control-plane/api";
import ServiceCard from "@/features/admin-panel/control-plane/components/ServiceCard/ServiceCard";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphIsLoadingSelector,
  chatQnAGraphIsRenderableSelector,
  chatQnAGraphNodesSelector,
  chatQnAGraphIsAutorefreshEnabledSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphSelectedServiceNode,
  setChatQnAGraphIsAutorefreshEnabled,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
import { ServiceData } from "@/features/admin-panel/control-plane/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";

const ControlPlaneTab = () => {
  useGetServicesDataQuery();

  const dispatch = useAppDispatch();
  const isLoading = useAppSelector(chatQnAGraphIsLoadingSelector);
  const isRenderable = useAppSelector(chatQnAGraphIsRenderableSelector);
  const isAutorefreshEnabled = useAppSelector(
    chatQnAGraphIsAutorefreshEnabledSelector,
  );

  const [getServicesData, { isFetching }] = useLazyGetServicesDataQuery();

  const handleAutorefreshChange = useCallback(
    (enabled: boolean) => {
      dispatch(setChatQnAGraphIsAutorefreshEnabled(enabled));
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
      Graph={ChatQnAGraph}
      ConfigPanel={ServiceCard}
      isAutorefreshEnabled={isAutorefreshEnabled}
      onAutorefreshChange={handleAutorefreshChange}
      onRefresh={handleRefresh}
      isFetching={isFetching}
    />
  );
};

const ChatQnAGraph = () => {
  const dispatch = useAppDispatch();
  const nodes = useAppSelector(chatQnAGraphNodesSelector);
  const edges = useAppSelector(chatQnAGraphEdgesSelector);

  const { colorScheme: colorMode } = useColorScheme();

  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node<Record<string, unknown>>[] }) => {
      dispatch(
        setChatQnAGraphSelectedServiceNode(nodes as Node<ServiceData>[]),
      );
    },
    [dispatch],
  );

  const handleNodesChange = (
    changes: NodeChange<Node<Record<string, unknown>>>[],
  ) => {
    dispatch(
      onChatQnAGraphNodesChange(changes as NodeChange<Node<ServiceData>>[]),
    );
  };

  const fitViewOptions: FitViewOptions = useMemo(
    () => ({
      padding: nodes.length > 9 ? 0.25 : 0.5,
    }),
    [nodes.length],
  );

  return (
    <PipelineGraph
      nodes={nodes}
      edges={edges}
      fitViewOptions={fitViewOptions}
      onNodesChange={handleNodesChange}
      onEdgesChange={onChatQnAGraphEdgesChange}
      onSelectionChange={handleSelectionChange}
      onConnect={onChatQnAGraphConnect}
      colorMode={colorMode}
    />
  );
};

export default ControlPlaneTab;
