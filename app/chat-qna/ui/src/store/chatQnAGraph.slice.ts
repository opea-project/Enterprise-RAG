// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Edge,
  EdgeChange,
  Node,
} from "@xyflow/react";
import { Connection, NodeChange } from "@xyflow/system";

import { ServicesParameters } from "@/api/models/system-fingerprint/appendArguments";
import { ServiceData } from "@/models/admin-panel/control-plane/serviceData";
import { RootState } from "@/store/index";
import { graphNodes } from "@/utils/chatQnAGraph";

export interface ServiceNodeChange {
  nodeId: string;
  argName: string;
  argValue: string | number | boolean;
}

interface ChatQnAGraphState {
  editModeEnabled: boolean;
  nodes: Node<ServiceData>[];
  edges: Edge[];
  loading: boolean;
  interactivityEnabled: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  nodesChangeList: ServiceNodeChange[];
}

const initialState: ChatQnAGraphState = {
  editModeEnabled: false,
  nodes: graphNodes,
  edges: [],
  loading: false,
  interactivityEnabled: false,
  selectedServiceNode: null,
  nodesChangeList: [],
};

export const chatQnAGraphSlice = createSlice({
  name: "chatQnAGraph",
  initialState,
  reducers: {
    onChatQnAGraphNodesChange: (
      state,
      action: PayloadAction<NodeChange<Node<ServiceData>>[]>,
    ) => {
      const changes = action.payload;
      state.nodes = applyNodeChanges(changes, [...state.nodes]);
    },
    onChatQnAGraphEdgesChange: (
      state,
      action: PayloadAction<EdgeChange<Edge>[]>,
    ) => {
      const changes = action.payload;
      state.edges = applyEdgeChanges(changes, state.edges);
    },
    onChatQnAGraphConnect: (
      state,
      action: PayloadAction<Edge | Connection>,
    ) => {
      const edgeParams = action.payload;
      state.edges = addEdge(edgeParams, state.edges);
    },
    setChatQnAGraphEditMode: (state, action: PayloadAction<boolean>) => {
      state.editModeEnabled = action.payload;
    },
    setChatQnAGraphEdges: (state, action: PayloadAction<Edge[]>) => {
      state.edges = [...action.payload];
    },
    setChatQnAGraphInitialNodes: (
      state,
      action: PayloadAction<ServicesParameters>,
    ) => {
      const fetchedArgs = Object.entries(action.payload);
      state.nodes = graphNodes.map((node) => {
        if (node.data.args) {
          let serviceArgs = [...node.data.args];
          for (const [fetchedArgName, fetchedArgValue] of fetchedArgs) {
            serviceArgs = serviceArgs.map((arg) =>
              arg.displayName === fetchedArgName
                ? { ...arg, value: fetchedArgValue }
                : { ...arg },
            );
          }
          return { ...node, data: { ...node.data, args: serviceArgs } };
        } else {
          return node;
        }
      });
    },
    setChatQnAGraphLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setChatQnAGraphSelectedServiceNode: (
      state,
      action: PayloadAction<Node<ServiceData>[]>,
    ) => {
      state.editModeEnabled = false;
      const nodes = action.payload;
      if (nodes.length && nodes[0] !== state.selectedServiceNode) {
        state.selectedServiceNode = nodes[0] as Node<ServiceData>;
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
  },
});

export const {
  setChatQnAGraphEditMode,
  onChatQnAGraphNodesChange,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphConnect,
  setChatQnAGraphEdges,
  setChatQnAGraphInitialNodes,
  setChatQnAGraphLoading,
  setChatQnAGraphSelectedServiceNode,
} = chatQnAGraphSlice.actions;
export const chatQnAGraphEditModeEnabledSelector = (state: RootState) =>
  state.chatQnAGraph.editModeEnabled;
export const chatQnAGraphNodesSelector = (state: RootState) =>
  state.chatQnAGraph.nodes;
export const chatQnAGraphEdgesSelector = (state: RootState) =>
  state.chatQnAGraph.edges;
export const chatQnAGraphLoadingSelector = (state: RootState) =>
  state.chatQnAGraph.loading;
export const chatQnAGraphSelectedServiceNodeSelector = (state: RootState) =>
  state.chatQnAGraph.selectedServiceNode;

export default chatQnAGraphSlice.reducer;
