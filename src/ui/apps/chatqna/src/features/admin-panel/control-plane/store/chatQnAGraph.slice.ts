// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  FetchedServiceDetails,
  FetchedServicesData,
  ServiceData,
  updateNodes,
} from "@intel-enterprise-rag-ui/control-plane";
import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Connection,
  Edge,
  EdgeChange,
  Node,
  NodeChange,
} from "@xyflow/react";

import {
  graphEdges,
  graphNodes,
  llmNodePositionNoGuards,
  vllmNodePositionNoGuards,
} from "@/features/admin-panel/control-plane/config/graph";
import { RootState } from "@/store/index";

interface ChatQnAGraphState {
  nodes: Node<ServiceData>[];
  edges: Edge[];
  isLoading: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  isRenderable: boolean;
  isAutorefreshEnabled: boolean;
}

const initialState: ChatQnAGraphState = {
  nodes: graphNodes,
  edges: [],
  isLoading: false,
  selectedServiceNode: null,
  isRenderable: false,
  isAutorefreshEnabled: false,
};

export const resetChatQnAGraph = createAsyncThunk(
  "chatQnAGraph/resetChatQnAGraph",
  (_, { dispatch }) => {
    dispatch(setChatQnAGraphSelectedServiceNode([]));
    dispatch(setChatQnAGraphIsLoading(true));
  },
);

export const setupChatQnAGraph = createAsyncThunk(
  "chatQnAGraph/setupChatQnAGraph",
  ({ parameters, details }: FetchedServicesData, { dispatch }) => {
    dispatch(setChatQnAGraphNodes({ parameters, details }));
    dispatch(setChatQnAGraphEdges(details));
    dispatch(setChatQnAGraphIsRenderable(true));
  },
);

export const chatQnAGraphSlice = createSlice({
  name: "chatQnAGraph",
  initialState,
  reducers: {
    onChatQnAGraphNodesChange: (
      state,
      action: PayloadAction<NodeChange<Node<ServiceData>>[]>,
    ) => {
      const changes = action.payload;
      state.nodes = applyNodeChanges(changes, [
        ...state.nodes,
      ]) as typeof state.nodes;
    },
    onChatQnAGraphEdgesChange: (
      state,
      action: PayloadAction<EdgeChange<Edge>[]>,
    ) => {
      const changes = action.payload;
      state.edges = applyEdgeChanges(changes, state.edges as Edge[]);
    },
    onChatQnAGraphConnect: (
      state,
      action: PayloadAction<Edge | Connection>,
    ) => {
      const edgeParams = action.payload;
      state.edges = addEdge(edgeParams, state.edges);
    },
    setChatQnAGraphEdges: (
      state,
      action: PayloadAction<FetchedServiceDetails>,
    ) => {
      const details = action.payload;
      const hasInputGuard = details.input_guard.status !== undefined;
      state.edges = hasInputGuard
        ? graphEdges.filter((edge) => edge.id !== "prompt_template-llm")
        : graphEdges;
    },
    setChatQnAGraphNodes: (
      state,
      action: PayloadAction<FetchedServicesData>,
    ) => {
      const fetchedServicesData = action.payload;
      state.nodes = updateNodes(
        graphNodes,
        fetchedServicesData,
        llmNodePositionNoGuards,
        vllmNodePositionNoGuards,
      ) as typeof state.nodes;
    },
    setChatQnAGraphSelectedServiceNode: (
      state,
      action: PayloadAction<Node<ServiceData>[]>,
    ) => {
      const nodes = action.payload;
      if (nodes.length && nodes[0] !== state.selectedServiceNode) {
        state.selectedServiceNode =
          nodes[0] as typeof state.selectedServiceNode;
      } else {
        state.selectedServiceNode = null;
      }
      state.nodes = [...state.nodes].map((node) => ({
        ...node,
        data: {
          ...node.data,
          selected: state.selectedServiceNode
            ? node.id === state.selectedServiceNode.id
            : false,
        },
      }));
    },
    setChatQnAGraphIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setChatQnAGraphIsRenderable: (state, action: PayloadAction<boolean>) => {
      state.isRenderable = action.payload;
    },
    setChatQnAGraphIsAutorefreshEnabled: (
      state,
      action: PayloadAction<boolean>,
    ) => {
      state.isAutorefreshEnabled = action.payload;
    },
    resetChatQnAGraphSlice: () => initialState,
  },
});

export const {
  onChatQnAGraphNodesChange,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphConnect,
  setChatQnAGraphEdges,
  setChatQnAGraphNodes,
  setChatQnAGraphIsLoading,
  setChatQnAGraphSelectedServiceNode,
  setChatQnAGraphIsRenderable,
  setChatQnAGraphIsAutorefreshEnabled,
  resetChatQnAGraphSlice,
} = chatQnAGraphSlice.actions;

export const chatQnAGraphNodesSelector = (state: RootState) =>
  state.chatQnAGraph.nodes;
export const chatQnAGraphEdgesSelector = (state: RootState) =>
  state.chatQnAGraph.edges;
export const chatQnAGraphIsLoadingSelector = (state: RootState) =>
  state.chatQnAGraph.isLoading;
export const chatQnAGraphSelectedServiceNodeSelector = (state: RootState) =>
  state.chatQnAGraph.selectedServiceNode;
export const chatQnAGraphIsRenderableSelector = (state: RootState) =>
  state.chatQnAGraph.isRenderable;
export const chatQnAGraphIsAutorefreshEnabledSelector = (state: RootState) =>
  state.chatQnAGraph.isAutorefreshEnabled;

export default chatQnAGraphSlice.reducer;
