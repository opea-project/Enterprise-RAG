// Copyright (C) 2024-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import {
  FetchedServicesData,
  ServiceNodeData,
  updateNodes,
} from "@intel-enterprise-rag-ui/control-plane";
import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Edge, Node } from "@xyflow/react";

import {
  graphEdges,
  graphNodes,
} from "@/features/admin-panel/control-plane/config/graph";
import { RootState } from "@/store/index";

interface DocSumGraphState {
  nodes: Node<ServiceNodeData>[];
  edges: Edge[];
  isLoading: boolean;
  selectedServiceNode: Node<ServiceNodeData> | null;
  isRenderable: boolean;
  isAutorefreshEnabled: boolean;
}

const initialState: DocSumGraphState = {
  nodes: graphNodes,
  edges: [],
  isLoading: false,
  selectedServiceNode: null,
  isRenderable: false,
  isAutorefreshEnabled: false,
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
      state.nodes = updateNodes(
        graphNodes,
        fetchedServicesData,
      ) as typeof state.nodes;
    },
    setDocSumGraphIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setDocSumGraphIsRenderable: (state, action: PayloadAction<boolean>) => {
      state.isRenderable = action.payload;
    },
    setDocSumGraphIsAutorefreshEnabled: (
      state,
      action: PayloadAction<boolean>,
    ) => {
      state.isAutorefreshEnabled = action.payload;
    },
    resetDocSumGraphSlice: () => initialState,
  },
});

export const {
  setDocSumGraphEdges,
  setDocSumGraphNodes,
  setDocSumGraphIsLoading,
  setDocSumGraphIsRenderable,
  setDocSumGraphIsAutorefreshEnabled,
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
export const docSumGraphIsAutorefreshEnabledSelector = (state: RootState) =>
  state.docSumGraph.isAutorefreshEnabled;

export default docSumGraphSlice.reducer;
