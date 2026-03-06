// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useColorScheme } from "@intel-enterprise-rag-ui/components";
import {
  ControlPlanePanel,
  PipelineGraph,
  ServiceData,
  useControlPlanePolling,
} from "@intel-enterprise-rag-ui/control-plane";
import { FitViewOptions, Node, NodeChange } from "@xyflow/react";
import { useCallback, useMemo } from "react";

import {
  useChangeArgumentsMutation,
  useGetServicesDataQuery,
  useLazyGetServicesDataQuery,
} from "@/features/admin-panel/control-plane/api";
import ServiceCard from "@/features/admin-panel/control-plane/components/ServiceCard/ServiceCard";
import {
  chatQnAGraphEdgesSelector,
  chatQnAGraphIsAutorefreshEnabledSelector,
  chatQnAGraphIsLoadingSelector,
  chatQnAGraphIsRenderableSelector,
  chatQnAGraphNodesSelector,
  onChatQnAGraphConnect,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphNodesChange,
  setChatQnAGraphIsAutorefreshEnabled,
  setChatQnAGraphSelectedServiceNode,
} from "@/features/admin-panel/control-plane/store/chatQnAGraph.slice";
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
  const [changeArguments] = useChangeArgumentsMutation();

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
      ConfigPanel={() => <ServiceCard changeArguments={changeArguments} />}
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
