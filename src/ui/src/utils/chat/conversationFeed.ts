// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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

export const handleError = (error: unknown): string => {
  if (typeof error === "string") {
    return error;
  }

  if (error instanceof Error) {
    if (error.message.includes("Guard:")) {
      const errorDetails = extractGuardError(error.message);
      return errorDetails ?? error.message;
    } else {
      return error.message;
    }
  } else {
    return JSON.stringify(error);
  }
};
