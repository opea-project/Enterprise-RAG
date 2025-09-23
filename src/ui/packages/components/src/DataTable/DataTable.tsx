// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataTable.scss";

import { LoadingIcon } from "@intel-enterprise-rag-ui/icons";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import classNames from "classnames";
import { useEffect, useState } from "react";

export type DataTableColumnDef<T> = ColumnDef<T>;

interface DataTableProps<T extends object> {
  /** Initial data to display in the table */
  defaultData: T[];
  /** Column definitions for the table */
  columns: DataTableColumnDef<T>[];
  /** If true, shows loading indicator */
  isDataLoading: boolean;
  /** If true, renders table in dense mode */
  dense?: boolean;
}

/**
 * Data table component for displaying tabular data with customizable columns and loading state.
 */
export const DataTable = <T extends object>({
  defaultData,
  columns,
  isDataLoading,
  dense,
}: DataTableProps<T>) => {
  const [data, setData] = useState<T[]>([]);

  useEffect(() => {
    setData(defaultData);
  }, [defaultData]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const getTableBody = () => {
    if (isDataLoading) {
      return (
        <tr>
          <td colSpan={100}>
            <div className="flex items-center justify-center">
              <LoadingIcon className="mr-2 animate-spin text-sm" />
              <p>Loading data...</p>
            </div>
          </td>
        </tr>
      );
    } else {
      if (table.getRowModel().rows.length === 0) {
        return (
          <tr>
            <td colSpan={100}>
              <p className="text-center">No data</p>
            </td>
          </tr>
        );
      } else {
        return table.getRowModel().rows.map((row) => (
          <tr key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ));
      }
    }
  };

  const tableClassNames = classNames("data-table", {
    "data-table--dense": dense,
  });

  return (
    <div>
      <table className={tableClassNames}>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>{getTableBody()}</tbody>
      </table>
    </div>
  );
};
