// Copyright (C) 2024-2025 Intel Corporation
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

import {
  FetchedServiceDetails,
  GuardrailParams,
  ServicesParameters,
} from "@/api/models/systemFingerprint";
import ServiceArgument from "@/models/admin-panel/control-plane/serviceArgument";
import {
  GuardrailArguments,
  ServiceData,
  ServiceDetails,
  ServiceStatus,
} from "@/models/admin-panel/control-plane/serviceData";
import { RootState } from "@/store/index";
import {
  graphEdges,
  graphNodes,
  LLM_NODE_POSITION_NO_GUARDS,
} from "@/utils/chatQnAGraph";

interface ChatQnAGraphState {
  editModeEnabled: boolean;
  nodes: Node<ServiceData>[];
  edges: Edge[];
  loading: boolean;
  hasInputGuard: boolean;
  hasOutputGuard: boolean;
  selectedServiceNode: Node<ServiceData> | null;
}

const initialState: ChatQnAGraphState = {
  editModeEnabled: false,
  nodes: graphNodes,
  edges: [],
  loading: false,
  hasInputGuard: false,
  hasOutputGuard: false,
  selectedServiceNode: null,
};

const updateServiceArgs = (
  args: ServiceArgument[],
  parameters: ServicesParameters,
): ServiceArgument[] =>
  args.map((arg) => {
    const fetchedArgValue = parameters[arg.displayName];
    return fetchedArgValue !== undefined &&
      !(fetchedArgValue instanceof GuardrailParams)
      ? { ...arg, value: fetchedArgValue }
      : arg;
  });

const updateGuardArgs = (
  guardArgs: GuardrailArguments,
  fetchedGuardArgs: GuardrailParams,
): GuardrailArguments => {
  const updatedGuardArgs: GuardrailArguments = { ...guardArgs };
  for (const scannerName in updatedGuardArgs) {
    updatedGuardArgs[scannerName] = updatedGuardArgs[scannerName].map(
      (scannerArg) => {
        const fetchedScannerArgValue =
          fetchedGuardArgs[scannerName][scannerArg.displayName];

        return {
          ...scannerArg,
          value: Array.isArray(fetchedScannerArgValue)
            ? fetchedScannerArgValue.join(",")
            : fetchedScannerArgValue,
        };
      },
    );
  }
  return updatedGuardArgs;
};

const updateNodeDetails = (
  node: Node<ServiceData>,
  fetchedDetails: FetchedServiceDetails,
  parameters: ServicesParameters,
): Node<ServiceData> => {
  const nodeId = node.data.id;
  let nodeDetails: ServiceDetails = {};
  let nodeStatus: ServiceStatus | undefined;

  if (fetchedDetails[nodeId]) {
    const { details, status } = fetchedDetails[nodeId];
    nodeDetails = details || {};
    nodeStatus = status as ServiceStatus;
  }

  if (node.data.args) {
    const serviceArgs = updateServiceArgs(node.data.args, parameters);
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        args: serviceArgs,
      },
    };
  } else if (node.data.guardArgs) {
    const fetchedGuardArgs =
      nodeId === "input_guard"
        ? parameters.input_guardrail_params
        : parameters.output_guardrail_params;

    const guardArgs = fetchedGuardArgs
      ? updateGuardArgs({ ...node.data.guardArgs }, fetchedGuardArgs)
      : { ...node.data.guardArgs };

    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        guardArgs,
      },
    };
  } else {
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
      },
    };
  }
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
    setChatQnAGraphEdges: (state) => {
      state.edges = state.hasInputGuard
        ? graphEdges.filter((edge) => edge.id !== "reranker-llm")
        : graphEdges;
    },
    setChatQnAGraphNodes: (
      state,
      action: PayloadAction<{
        parameters: ServicesParameters;
        fetchedDetails: FetchedServiceDetails;
      }>,
    ) => {
      const { parameters, fetchedDetails } = action.payload;
      const updatedNodes = graphNodes
        .map((node) => updateNodeDetails(node, fetchedDetails, parameters))
        .filter((node) => node.data.status);

      const updatedNodesIds = updatedNodes.map(({ id }) => id);
      const llmNodeIndex = updatedNodes.findIndex(({ id }) => id === "llm");

      if (
        !updatedNodesIds.includes("input_guard") &&
        !updatedNodesIds.includes("output_guard") &&
        llmNodeIndex !== -1
      ) {
        updatedNodes[llmNodeIndex].position = LLM_NODE_POSITION_NO_GUARDS;
      }

      state.nodes = updatedNodes;
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
    setHasInputGuard: (state, action: PayloadAction<boolean>) => {
      state.hasInputGuard = action.payload;
    },
    setHasOutputGuard: (state, action: PayloadAction<boolean>) => {
      state.hasOutputGuard = action.payload;
    },
  },
});

export const {
  setChatQnAGraphEditMode,
  onChatQnAGraphNodesChange,
  onChatQnAGraphEdgesChange,
  onChatQnAGraphConnect,
  setChatQnAGraphEdges,
  setChatQnAGraphNodes,
  setChatQnAGraphLoading,
  setChatQnAGraphSelectedServiceNode,
  setHasInputGuard,
  setHasOutputGuard,
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
export const hasInputGuardSelector = (state: RootState) =>
  state.chatQnAGraph.hasInputGuard;
export const hasOutputGuardSelector = (state: RootState) =>
  state.chatQnAGraph.hasOutputGuard;

export default chatQnAGraphSlice.reducer;
