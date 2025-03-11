// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Edge,
  EdgeChange,
  Node,
} from "@xyflow/react";
import { Connection, NodeChange } from "@xyflow/system";

import { addNotification } from "@/components/ui/Notifications/notifications.slice";
import { getArguments } from "@/features/admin-panel/control-plane/api/getArguments";
import { getChatQAStatus } from "@/features/admin-panel/control-plane/api/getChatQAStatus";
import { postArguments } from "@/features/admin-panel/control-plane/api/postArguments";
import {
  graphEdges,
  graphNodes,
  llmNodePositionNoGuards,
  vllmNodePositionNoGuards,
} from "@/features/admin-panel/control-plane/config/chatQnAGraph";
import {
  ServiceData,
  ServiceDetails,
  ServiceStatus,
} from "@/features/admin-panel/control-plane/types";
import {
  ChangeArgumentsRequestData,
  FetchedServiceDetails,
  ServicesParameters,
} from "@/features/admin-panel/control-plane/types/systemFingerprint";
import { RootState } from "@/store/index";

interface ChatQnAGraphState {
  editModeEnabled: boolean;
  nodes: Node<ServiceData>[];
  edges: Edge[];
  loading: boolean;
  hasInputGuard: boolean;
  hasOutputGuard: boolean;
  selectedServiceNode: Node<ServiceData> | null;
  canBeRendered: boolean;
}

const initialState: ChatQnAGraphState = {
  editModeEnabled: false,
  nodes: graphNodes,
  edges: [],
  loading: false,
  hasInputGuard: false,
  hasOutputGuard: false,
  selectedServiceNode: null,
  canBeRendered: false,
};

export const fetchGraphData = createAsyncThunk(
  "chatQnAGraph/fetchGraph",
  async (_, { dispatch }) => {
    dispatch(setChatQnAGraphEditMode(false));
    dispatch(setChatQnAGraphSelectedServiceNode([]));
    dispatch(setChatQnAGraphLoading(true));

    try {
      const [fetchedDetails, parameters] = await Promise.all([
        getChatQAStatus(),
        getArguments(),
      ]);

      if (fetchedDetails && parameters) {
        const hasInputGuard = fetchedDetails.input_guard.status !== undefined;
        const hasOutputGuard = fetchedDetails.output_guard.status !== undefined;
        dispatch(setHasInputGuard(hasInputGuard));
        dispatch(setHasOutputGuard(hasOutputGuard));

        dispatch(
          setChatQnAGraphNodes({
            parameters,
            fetchedDetails: fetchedDetails ?? {},
          }),
        );
        dispatch(setChatQnAGraphEdges());
        dispatch(setCanBeRendered(true));
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
      dispatch(setCanBeRendered(false));
    } finally {
      dispatch(setChatQnAGraphLoading(false));
    }
  },
);

export const changeServiceArguments = createAsyncThunk(
  "chatQnAGraph/changeServiceArguments",
  async (
    { name, data }: { name: string; data: ChangeArgumentsRequestData },
    { dispatch },
  ) => {
    dispatch(setChatQnAGraphEditMode(false));
    dispatch(setChatQnAGraphSelectedServiceNode([]));
    dispatch(setChatQnAGraphLoading(true));

    try {
      const postArgumentsRequestBody = [{ name, data }];
      await postArguments(postArgumentsRequestBody);
      dispatch(fetchGraphData());
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to change arguments";
      dispatch(addNotification({ severity: "error", text: errorMessage }));
    }
  },
);

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

  if (node.data.llmArgs) {
    const { llmArgs } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        llmArgs,
      },
    };
  } else if (node.data.rerankerArgs) {
    const { rerankerArgs } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        rerankerArgs,
      },
    };
  } else if (node.data.retrieverArgs) {
    const { retrieverArgs } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        retrieverArgs,
      },
    };
  } else if (node.data.inputGuardArgs) {
    const { inputGuardArgs } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        inputGuardArgs,
      },
    };
  } else if (node.data.outputGuardArgs) {
    const { outputGuardArgs } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        outputGuardArgs,
      },
    };
  } else if (node.data.promptTemplate !== undefined) {
    const { promptTemplate } = parameters;
    return {
      ...node,
      data: {
        ...node.data,
        details: nodeDetails,
        status: nodeStatus,
        promptTemplate,
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
        ? graphEdges.filter((edge) => edge.id !== "prompt_template-llm")
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
    setCanBeRendered: (state, action: PayloadAction<boolean>) => {
      state.canBeRendered = action.payload;
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
  setCanBeRendered,
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
export const chatQnAGraphCanBeRenderedSelector = (state: RootState) =>
  state.chatQnAGraph.canBeRendered;

export default chatQnAGraphSlice.reducer;
