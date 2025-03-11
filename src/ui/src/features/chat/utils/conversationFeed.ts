// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { UpdatedChatMessage } from "@/features/chat/types";

export const extractGuardError = (errorString: string): string | null => {
  try {
    // Extract the JSON part from the error string
    const jsonMatch = errorString.match(/Guard: ({.*})/);
    if (!jsonMatch || jsonMatch.length < 2) {
      throw new Error("Guard error occurred but couldn't extract its details.");
    }

    // Parse the extracted JSON
    const errorJson = JSON.parse(jsonMatch[1]);

    // Extract the detail field
    const detailJson = JSON.parse(errorJson.error);
    if (detailJson.detail) {
      return detailJson.detail;
    } else {
      throw new Error();
    }
  } catch (error) {
    console.error("Failed to extract detail:", error);
    if (error instanceof Error) {
      return error.message;
    } else {
      return JSON.stringify(error);
    }
  }
};

export const handleError = (error: unknown): string | UpdatedChatMessage => {
  if (typeof error === "string") {
    return { text: error, isError: false };
  }

  if (error instanceof Error) {
    if (error.name === "AbortError") {
      return "";
    }

    if (error.name === "TypeError" && error.message === "Failed to fetch") {
      return {
        text: `${error.message}. This is probably network related error. Please contact your system administrator for further details.`,
        isError: true,
      };
    }

    if (error.message.startsWith("Guard:")) {
      const errorDetails = extractGuardError(error.message);
      return errorDetails ?? { text: error.message, isError: false };
    } else {
      return { text: error.message, isError: true };
    }
  } else {
    return { text: JSON.stringify(error), isError: true };
  }
};
