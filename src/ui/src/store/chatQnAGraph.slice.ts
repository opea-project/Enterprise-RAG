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

import {
  FetchedServiceDetails,
  GuardrailParams,
  ServicesParameters,
} from "@/api/models/systemFingerprint";
import { inputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/inputGuard";
import { outputGuardArguments } from "@/models/admin-panel/control-plane/guardrails/outputGuard";
import {
  ServiceData,
  ServiceDetails,
  ServiceStatus,
} from "@/models/admin-panel/control-plane/serviceData";
import { RootState } from "@/store/index";
import { graphEdges, graphNodes } from "@/utils/chatQnAGraph";

interface ChatQnAGraphState {
  editModeEnabled: boolean;
  nodes: Node<ServiceData>[];
  edges: Edge[];
  loading: boolean;
  interactivityEnabled: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  promptRequestParams: ServicesParameters;
}

const initialState: ChatQnAGraphState = {
  editModeEnabled: false,
  nodes: graphNodes,
  edges: [],
  loading: false,
  interactivityEnabled: false,
  selectedServiceNode: null,
  promptRequestParams: {},
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
      const nodesIds = state.nodes.map(({ id }) => id);
      const graphHasInputGuard = nodesIds.includes("input_guard");

      state.edges = graphHasInputGuard
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
      const fetchedArgs = Object.entries(parameters);
      const fetchedDetailedServices = Object.keys(fetchedDetails);
      const updatedNodes = graphNodes
        .map((node) => {
          const nodeId = node.data.id;

          let nodeDetails: ServiceDetails = {};
          let nodeStatus;
          if (fetchedDetailedServices.includes(nodeId)) {
            const { details, status } = fetchedDetails[nodeId];
            if (details) {
              nodeDetails = details;
            }
            if (status) {
              nodeStatus = status as ServiceStatus;
            }
          }

          if (node.data.args) {
            let serviceArgs = [...node.data.args];
            for (const [fetchedArgName, fetchedArgValue] of fetchedArgs) {
              serviceArgs = serviceArgs.map((arg) =>
                arg.displayName === fetchedArgName &&
                !(fetchedArgValue instanceof GuardrailParams) &&
                fetchedArgValue !== undefined
                  ? { ...arg, value: fetchedArgValue }
                  : { ...arg },
              );
            }
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
            const updatedGuardArgs = { ...node.data.guardArgs };
            let fetchedGuardArgs: GuardrailParams | undefined = {};
            if (node.data.id === "input_guard") {
              fetchedGuardArgs = parameters.input_guardrail_params;
            } else if (node.data.id === "output_guard") {
              fetchedGuardArgs = parameters.output_guardrail_params;
            }

            if (fetchedGuardArgs !== undefined) {
              for (const scannerName in updatedGuardArgs) {
                updatedGuardArgs[scannerName] = updatedGuardArgs[
                  scannerName
                ].map((scannerArg) => {
                  const scannerArgName = scannerArg.displayName;
                  let fetchedScannerArgValue =
                    fetchedGuardArgs[scannerName][scannerArgName];
                  if (Array.isArray(fetchedScannerArgValue)) {
                    fetchedScannerArgValue = fetchedScannerArgValue.join(",");
                  }

                  return {
                    ...scannerArg,
                    value: fetchedScannerArgValue,
                  };
                });
              }
            }

            return {
              ...node,
              data: {
                ...node.data,
                details: nodeDetails,
                status: nodeStatus,
                guardArgs: updatedGuardArgs,
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
        })
        .filter((node) => node.data.status);

      const updatedNodesIds = updatedNodes.map(({ id }) => id);
      const llmNodeIndex = updatedNodes.findIndex(({ id }) => id === "llm");

      if (
        !updatedNodesIds.includes("input_guard") &&
        !updatedNodesIds.includes("output_guard") &&
        llmNodeIndex !== -1
      ) {
        updatedNodes[llmNodeIndex].position = { x: 640, y: 144 };
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
    setPromptRequestParams: (state, action) => {
      const serviceParams = Object.fromEntries(
        Object.entries(action.payload).filter(
          ([, value]) =>
            typeof value === "string" ||
            typeof value === "number" ||
            typeof value === "boolean" ||
            value === null,
        ),
      ) as ServicesParameters;

      const graphNodesIds = state.nodes.map(({ id }) => id);
      let guardParams;
      if (
        graphNodesIds.includes("input_guard") &&
        graphNodesIds.includes("output_guard")
      ) {
        guardParams = Object.fromEntries(
          Object.entries(action.payload).filter(([key]) =>
            ["input_guardrail_params", "output_guardrail_params"].includes(key),
          ),
        );

        const supportedInputScanners = Object.keys(inputGuardArguments);
        const supportedOutputScanners = Object.keys(outputGuardArguments);
        const inputGuardParams = Object.fromEntries(
          Object.entries(guardParams.input_guardrail_params || {}).filter(
            ([scannerName]) => supportedInputScanners.includes(scannerName),
          ),
        );
        const outputGuardParams = Object.fromEntries(
          Object.entries(guardParams.output_guardrail_params || {}).filter(
            ([scannerName]) => supportedOutputScanners.includes(scannerName),
          ),
        );
        guardParams = Object.fromEntries(
          Object.entries({
            input_guardrail_params: inputGuardParams,
            output_guardrail_params: outputGuardParams,
          }).filter(
            ([, value]) =>
              typeof value === "object" && Object.keys(value).length > 0,
          ),
        );

        state.promptRequestParams = {
          ...serviceParams,
          ...guardParams,
        };
      } else {
        state.promptRequestParams = {
          ...serviceParams,
        };
      }
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
  setPromptRequestParams,
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
export const selectPromptRequestParams = (state: RootState) =>
  state.chatQnAGraph.promptRequestParams;

export default chatQnAGraphSlice.reducer;
