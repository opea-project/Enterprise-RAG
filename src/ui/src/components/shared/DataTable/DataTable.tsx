// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataTable.scss";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useState } from "react";

import LoadingIcon from "@/components/icons/LoadingIcon/LoadingIcon";

interface DataTableProps<T extends object> {
  defaultData: T[];
  columns: ColumnDef<T>[];
  isDataLoading: boolean;
}

const DataTable = <T extends object>({
  defaultData,
  columns,
  isDataLoading,
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
              <LoadingIcon className="mr-2 text-sm" />
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

  return (
    <div>
      <table>
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

export default DataTable;
