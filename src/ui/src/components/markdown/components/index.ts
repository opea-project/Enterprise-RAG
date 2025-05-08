// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Components } from "react-markdown";

import { Code, Pre } from "@/components/markdown/components/code/Code";
import {
  ListItem,
  OrderedList,
  UnorderedList,
} from "@/components/markdown/components/lists/Lists";
import { A, Hr, Img } from "@/components/markdown/components/other/Other";
import {
  Table,
  TableCell,
  TableHeaderCell,
  TableRow,
} from "@/components/markdown/components/tables/Tables";
import {
  Blockquote,
  Del,
  Em,
  H1,
  H2,
  H3,
  H4,
  H5,
  H6,
  P,
  Strong,
} from "@/components/markdown/components/typography/Typography";

export const customMarkdownComponents: Partial<Components> = {
  // Typography
  h1: H1,
  h2: H2,
  h3: H3,
  h4: H4,
  h5: H5,
  h6: H6,

  p: P,
  strong: Strong,
  em: Em,
  del: Del,
  blockquote: Blockquote,

  // Lists
  ul: UnorderedList,
  ol: OrderedList,
  li: ListItem,

  // Code
  code: Code,
  pre: Pre,

  // Tables
  table: Table,
  tr: TableRow,
  th: TableHeaderCell,
  td: TableCell,

  // Other
  a: A,
  img: Img,
  hr: Hr,
};
