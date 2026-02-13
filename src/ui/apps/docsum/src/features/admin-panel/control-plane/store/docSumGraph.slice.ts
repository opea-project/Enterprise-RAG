// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  ServiceNodeData,
  ServiceStatus,
} from "@intel-enterprise-rag-ui/control-plane";
import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Edge, Node } from "@xyflow/react";

import {
  graphEdges,
  graphNodes,
} from "@/features/admin-panel/control-plane/config/graph";
import { ServiceDetails } from "@/features/admin-panel/control-plane/types";
import { FetchedServicesData } from "@/features/admin-panel/control-plane/types/api";
import { RootState } from "@/store/index";

interface DocSumGraphState {
  nodes: Node<ServiceNodeData>[];
  edges: Edge[];
  isLoading: boolean;
  selectedServiceNode: Node<ServiceNodeData> | null;
  isRenderable: boolean;
}

const initialState: DocSumGraphState = {
  nodes: graphNodes,
  edges: [],
  isLoading: false,
  selectedServiceNode: null,
  isRenderable: false,
};

export const resetDocSumGraph = createAsyncThunk(
  "docSumGraph/resetDocSumGraph",
  (_, { dispatch }) => {
    dispatch(setDocSumGraphIsLoading(true));
  },
);

export const setupDocSumGraph = createAsyncThunk(
  "docSumGraph/setupDocSumGraph",
  ({ details }: FetchedServicesData, { dispatch }) => {
    dispatch(setDocSumGraphNodes({ details }));
    dispatch(setDocSumGraphEdges());
    dispatch(setDocSumGraphIsRenderable(true));
  },
);

const updateNodes = (fetchedServicesData: FetchedServicesData) => {
  const graphNodes = [...initialState.nodes];

  const updatedNodes = graphNodes
    .map((node) => updateNodeDetails(node, fetchedServicesData))
    .filter((node) => node.data.status);

  return updatedNodes;
};

const updateNodeDetails = (
  node: Node<ServiceNodeData>,
  fetchedServicesData: FetchedServicesData,
): Node<ServiceNodeData> => {
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

export const docSumGraphSlice = createSlice({
  name: "docSumGraph",
  initialState,
  reducers: {
    setDocSumGraphEdges: (state) => {
      state.edges = graphEdges;
    },
    setDocSumGraphNodes: (
      state,
      action: PayloadAction<FetchedServicesData>,
    ) => {
      const fetchedServicesData = action.payload;
      state.nodes = updateNodes(fetchedServicesData) as typeof state.nodes;
    },
    setDocSumGraphIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setDocSumGraphIsRenderable: (state, action: PayloadAction<boolean>) => {
      state.isRenderable = action.payload;
    },
    resetDocSumGraphSlice: () => initialState,
  },
});

export const {
  setDocSumGraphEdges,
  setDocSumGraphNodes,
  setDocSumGraphIsLoading,
  setDocSumGraphIsRenderable,
  resetDocSumGraphSlice,
} = docSumGraphSlice.actions;

export const docSumGraphNodesSelector = (state: RootState) =>
  state.docSumGraph.nodes;
export const docSumGraphEdgesSelector = (state: RootState) =>
  state.docSumGraph.edges;
export const docSumGraphIsLoadingSelector = (state: RootState) =>
  state.docSumGraph.isLoading;
export const docSumGraphIsRenderableSelector = (state: RootState) =>
  state.docSumGraph.isRenderable;

export default docSumGraphSlice.reducer;
