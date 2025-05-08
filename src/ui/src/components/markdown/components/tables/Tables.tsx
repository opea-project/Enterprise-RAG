// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PropsWithChildren, TdHTMLAttributes, ThHTMLAttributes } from "react";

import styles from "./Tables.module.scss";

export const Table = ({ children }: PropsWithChildren) => (
  <table className={styles.table}>{children}</table>
);

export const TableRow = ({ children }: PropsWithChildren) => (
  <tr className={styles.tr}>{children}</tr>
);

type TableHeaderCellProps = PropsWithChildren<
  Pick<ThHTMLAttributes<HTMLTableCellElement>, "colSpan" | "rowSpan" | "style">
>;

export const TableHeaderCell = ({
  colSpan,
  rowSpan,
  style,
  children,
}: TableHeaderCellProps) => (
  <th className={styles.th} colSpan={colSpan} rowSpan={rowSpan} style={style}>
    {children}
  </th>
);

type TableCellProps = PropsWithChildren<
  Pick<TdHTMLAttributes<HTMLTableCellElement>, "colSpan" | "rowSpan" | "style">
>;

export const TableCell = ({
  colSpan,
  rowSpan,
  style,
  children,
}: TableCellProps) => (
  <td className={styles.td} colSpan={colSpan} rowSpan={rowSpan} style={style}>
    {children}
  </td>
);
