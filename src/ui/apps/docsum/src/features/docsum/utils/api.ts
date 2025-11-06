// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { SummaryUpdateHandler } from "@/features/docsum/api/types";

const extractBase64FromDataUrl = (dataUrl: string): string => {
  const base64Index = dataUrl.indexOf("base64,");
  if (base64Index === -1) {
    throw new Error("Invalid data URL format");
  }
  return dataUrl.substring(base64Index + 7);
};

const getContentType = (file: File): string => {
  const extension = file.name.split(".").pop()?.toLowerCase();

  // debugs before backend fixes
  if (extension === "pdf") {
    return "application/pdf";
  }

  if (file.type && file.type !== "application/octet-stream") {
    return file.type;
  }

  switch (extension) {
    case "doc":
      return "application/msword";
    case "docx":
      return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    case "md":
      return "text/plain";
    default:
      return "text/plain";
  }
};

const documentToBase64 = (document: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(document);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (error) => reject(error);
  });

const handleSummaryStreamResponse = async (
  response: Response,
  onSummaryUpdate: SummaryUpdateHandler,
) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder("utf-8");

  if (!reader) return;

  let done = false;
  do {
    const result = await reader.read();
    done = result?.done ?? true;

    if (result?.value) {
      const decodedValue = decoder.decode(result.value, { stream: true });
      console.log("Raw decoded value:", JSON.stringify(decodedValue));

      const events = decodedValue.split("\n\n");

      for (const event of events) {
        if (event.startsWith("data:")) {
          // skip to the next iteration if event data message is a keyword indicating that stream has finished
          if (event.includes("[DONE]") || event.includes("</s>")) {
            continue;
          }

          // extract chunk of text from event data message
          let newTextChunk = event.slice(6);
          let quoteRegex = /(?<!\\)'/g;
          if (newTextChunk.startsWith('"')) {
            quoteRegex = /"/g;
          }
          newTextChunk = newTextChunk
            .replace(quoteRegex, "")
            .replace(/\\t/g, "  \t")
            .replace(/\\n\\n/g, "  \n\n")
            .replace(/\\n/g, "  \n");

          onSummaryUpdate(newTextChunk);
        }
      }
    }
  } while (!done);
};

const convertToApiFileData = (fileData: {
  name: string;
  base64: string;
  type: string;
}): { filename: string; data64: string; content_type: string } => {
  return {
    filename: fileData.name,
    data64: extractBase64FromDataUrl(fileData.base64),
    content_type: fileData.type,
  };
};

const transformResponseError = (response: Response) => ({
  error: {
    status: response.status,
    data: `Error ${response.status}: ${response.statusText}`,
  },
});

export {
  convertToApiFileData,
  documentToBase64,
  extractBase64FromDataUrl,
  getContentType,
  handleSummaryStreamResponse,
  transformResponseError,
};
