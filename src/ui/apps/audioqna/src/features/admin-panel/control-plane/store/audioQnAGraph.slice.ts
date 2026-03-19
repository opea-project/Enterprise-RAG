// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ServiceStatus } from "@intel-enterprise-rag-ui/control-plane";
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
import {
  ServiceData,
  ServiceDetails,
} from "@/features/admin-panel/control-plane/types";
import {
  FetchedServiceDetails,
  FetchedServicesData,
} from "@/features/admin-panel/control-plane/types/api";
import { RootState } from "@/store/index";

interface AudioQnAGraphState {
  nodes: Node<ServiceData>[];
  edges: Edge[];
  isLoading: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  isRenderable: boolean;
}

const initialState: AudioQnAGraphState = {
  nodes: graphNodes,
  edges: [],
  isLoading: false,
  selectedServiceNode: null,
  isRenderable: false,
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
  ({ details }: FetchedServicesData, { dispatch }) => {
    dispatch(setAudioQnAGraphNodes({ details }));
    dispatch(setAudioQnAGraphEdges(details));
    dispatch(setAudioQnAGraphIsRenderable(true));
  },
);

const updateNodes = (fetchedServicesData: FetchedServicesData) => {
  const updatedNodes = graphNodes
    .map((node) => updateNodeDetails(node, fetchedServicesData))
    .filter((node) => node.data.status);

  const updatedNodesIds = updatedNodes.map(({ id }) => id);
  const llmNodeIndex = updatedNodes.findIndex(({ id }) => id === "llm");
  const vllmNodeIndex = updatedNodes.findIndex(({ id }) => id === "vllm");

  if (
    !updatedNodesIds.includes("input_guard") &&
    !updatedNodesIds.includes("output_guard") &&
    llmNodeIndex !== -1
  ) {
    updatedNodes[llmNodeIndex].position = llmNodePositionNoGuards;
  }

  if (
    !updatedNodesIds.includes("input_guard") &&
    !updatedNodesIds.includes("output_guard") &&
    vllmNodeIndex !== -1
  ) {
    updatedNodes[vllmNodeIndex].position = vllmNodePositionNoGuards;
  }

  return updatedNodes;
};

const updateNodeDetails = (
  node: Node<ServiceData>,
  fetchedServicesData: FetchedServicesData,
): Node<ServiceData> => {
  const nodeId = node.data.id;
  let nodeDetails: ServiceDetails = {};
  let nodeStatus: ServiceStatus | undefined;

  const { details: serviceDetails } = fetchedServicesData;
  if (serviceDetails[nodeId]) {
    const { details, status } = serviceDetails[nodeId];
    nodeDetails = details || {};
    nodeStatus = status as ServiceStatus;
  }

  return {
    ...node,
    data: {
      ...node.data,
      details: nodeDetails,
      status: nodeStatus,
    },
  };
};

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
      state.nodes = updateNodes(fetchedServicesData) as typeof state.nodes;
    },
    setAudioQnAGraphSelectedServiceNode: (
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
    setAudioQnAGraphIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setAudioQnAGraphIsRenderable: (state, action: PayloadAction<boolean>) => {
      state.isRenderable = action.payload;
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

export default audioQnAGraphSlice.reducer;
