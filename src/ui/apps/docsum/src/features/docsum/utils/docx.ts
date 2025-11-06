// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Document, Packer, Paragraph, TextRun } from "docx";

export const createDocxFromSummary = async (summary: string): Promise<Blob> => {
  const paragraphs = summary.split("\n").map(
    (text) =>
      new Paragraph({
        children: [new TextRun({ text })],
      }),
  );

  const doc = new Document({
    sections: [
      {
        properties: {},
        children: paragraphs,
      },
    ],
  });
  return await Packer.toBlob(doc);
};
