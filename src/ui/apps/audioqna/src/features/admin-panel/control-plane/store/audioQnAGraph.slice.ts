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
  llmModelServerNodePositionNoGuards,
  llmNodePositionNoGuards,
} from "@/features/admin-panel/control-plane/config/graph";
import { RootState } from "@/store/index";

interface AudioQnAGraphState {
  nodes: Node<ServiceData>[];
  edges: Edge[];
  isLoading: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  isRenderable: boolean;
  isAutorefreshEnabled: boolean;
}

const initialState: AudioQnAGraphState = {
  nodes: graphNodes,
  edges: [],
  isLoading: false,
  selectedServiceNode: null,
  isRenderable: false,
  isAutorefreshEnabled: false,
};

export const resetAudioQnAGraph = createAsyncThunk(
  "audioQnAGraph/resetAudioQnAGraph",
  (_, { dispatch }) => {
    dispatch(setAudioQnAGraphSelectedServiceNode([]));
    dispatch(setAudioQnAGraphIsLoading(true));
  },
);

export const setupAudioQnAGraph = createAsyncThunk(
  "audioQnAGraph/setupAudioQnAGraph",
  ({ details, parameters }: FetchedServicesData, { dispatch }) => {
    dispatch(setAudioQnAGraphNodes({ details, parameters }));
    dispatch(setAudioQnAGraphEdges(details));
    dispatch(setAudioQnAGraphIsRenderable(true));
  },
);

export const audioQnAGraphSlice = createSlice({
  name: "audioQnAGraph",
  initialState,
  reducers: {
    onAudioQnAGraphNodesChange: (
      state,
      action: PayloadAction<NodeChange<Node<ServiceData>>[]>,
    ) => {
      const changes = action.payload;
      state.nodes = applyNodeChanges(changes, [
        ...state.nodes,
      ]) as typeof state.nodes;
    },
    onAudioQnAGraphEdgesChange: (
      state,
      action: PayloadAction<EdgeChange<Edge>[]>,
    ) => {
      const changes = action.payload;
      state.edges = applyEdgeChanges(changes, state.edges as Edge[]);
    },
    onAudioQnAGraphConnect: (
      state,
      action: PayloadAction<Edge | Connection>,
    ) => {
      const edgeParams = action.payload;
      state.edges = addEdge(edgeParams, state.edges);
    },
    setAudioQnAGraphEdges: (
      state,
      action: PayloadAction<FetchedServiceDetails>,
    ) => {
      const details = action.payload;
      const hasInputGuard = details.input_guard.status !== undefined;
      state.edges = hasInputGuard
        ? graphEdges.filter((edge) => edge.id !== "prompt_template-llm")
        : graphEdges;
    },
    setAudioQnAGraphNodes: (
      state,
      action: PayloadAction<FetchedServicesData>,
    ) => {
      const fetchedServicesData = action.payload;
      const newNodes = updateNodes(
        graphNodes,
        fetchedServicesData,
        llmNodePositionNoGuards,
        llmModelServerNodePositionNoGuards,
      ) as typeof state.nodes;

      if (state.selectedServiceNode) {
        const selectedId = state.selectedServiceNode.id;
        state.nodes = newNodes.map((node) =>
          node.id === selectedId
            ? {
                ...node,
                selected: true,
                data: { ...node.data, selected: true },
              }
            : node,
        ) as typeof state.nodes;
      } else {
        state.nodes = newNodes;
      }
    },
    setAudioQnAGraphSelectedServiceNode: (
      state,
      action: PayloadAction<Node<ServiceData>[]>,
    ) => {
      const nodes = action.payload;
      if (nodes.length) {
        const incomingNode = nodes[0] as typeof state.selectedServiceNode;
        if (incomingNode?.id !== state.selectedServiceNode?.id) {
          state.selectedServiceNode = incomingNode;
        }
        // same id: keep existing selectedServiceNode to preserve unsaved form state
      } else {
        state.selectedServiceNode = null;
      }
      const selectedId = state.selectedServiceNode?.id ?? null;
      state.nodes = [...state.nodes].map((node) => ({
        ...node,
        selected: selectedId ? node.id === selectedId : false,
        data: {
          ...node.data,
          selected: selectedId ? node.id === selectedId : false,
        },
      }));
    },
    setAudioQnAGraphIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setAudioQnAGraphIsRenderable: (state, action: PayloadAction<boolean>) => {
      state.isRenderable = action.payload;
    },
    setAudioQnAGraphIsAutorefreshEnabled: (
      state,
      action: PayloadAction<boolean>,
    ) => {
      state.isAutorefreshEnabled = action.payload;
    },
    resetAudioQnAGraphSlice: () => initialState,
  },
});

export const {
  onAudioQnAGraphNodesChange,
  onAudioQnAGraphEdgesChange,
  onAudioQnAGraphConnect,
  setAudioQnAGraphEdges,
  setAudioQnAGraphNodes,
  setAudioQnAGraphIsLoading,
  setAudioQnAGraphSelectedServiceNode,
  setAudioQnAGraphIsRenderable,
  setAudioQnAGraphIsAutorefreshEnabled,
  resetAudioQnAGraphSlice,
} = audioQnAGraphSlice.actions;

export const audioQnAGraphNodesSelector = (state: RootState) =>
  state.audioQnAGraph.nodes;
export const audioQnAGraphEdgesSelector = (state: RootState) =>
  state.audioQnAGraph.edges;
export const audioQnAGraphIsLoadingSelector = (state: RootState) =>
  state.audioQnAGraph.isLoading;
export const audioQnAGraphSelectedServiceNodeSelector = (state: RootState) =>
  state.audioQnAGraph.selectedServiceNode;
export const audioQnAGraphIsRenderableSelector = (state: RootState) =>
  state.audioQnAGraph.isRenderable;
export const audioQnAGraphIsAutorefreshEnabledSelector = (state: RootState) =>
  state.audioQnAGraph.isAutorefreshEnabled;

export default audioQnAGraphSlice.reducer;
