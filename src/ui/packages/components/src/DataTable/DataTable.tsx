// Copyright (C) 2024-2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "./DataTable.scss";

import {
  LoadingIcon,
  SortDownIcon,
  SortUpDownIcon,
  SortUpIcon,
} from "@intel-enterprise-rag-ui/icons";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import classNames from "classnames";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

interface DataTableProps<T extends object> {
  /** Default data for the table */
  defaultData: T[];
  /** Column definitions for the table */
  columns: ColumnDef<T>[];
  /** Flag indicating if data is currently loading */
  isDataLoading: boolean;
  /** If true, applies a denser layout */
  dense?: boolean;
  /** Controlled global filter value */
  globalFilter?: string;
  /** Callback when the global filter changes */
  onGlobalFilterChange?: (value: string) => void;
  /** Additional class names for the table */
  className?: string;
}

export const DataTable = <T extends object>({
  defaultData,
  columns,
  isDataLoading,
  dense,
  globalFilter,
  onGlobalFilterChange,
  className = "",
}: DataTableProps<T>) => {
  const [data, setData] = useState(() => defaultData);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [internalGlobalFilter, setInternalGlobalFilter] = useState("");

  // Compute estimated row height based on dense prop
  // Dense mode: h-8 = 32px, Normal mode: h-12 = 48px
  const estimatedRowHeight = useMemo(() => (dense ? 32 : 48), [dense]);

  useEffect(() => {
    setData(defaultData);
  }, [defaultData]);

  const effectiveGlobalFilter = useMemo(
    () => globalFilter ?? internalGlobalFilter,
    [globalFilter, internalGlobalFilter],
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      globalFilter: effectiveGlobalFilter,
    },
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onGlobalFilterChange: onGlobalFilterChange ?? setInternalGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
  });

  const rows = table.getRowModel().rows;
  const scrollParentRef = useRef<HTMLTableSectionElement | null>(null);
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollParentRef.current,
    estimateSize: () => estimatedRowHeight,
    overscan: 6,
  });

  const virtualItems = rowVirtualizer.getVirtualItems();
  const paddingTop = virtualItems.length > 0 ? virtualItems[0].start : 0;
  const paddingBottom =
    virtualItems.length > 0
      ? rowVirtualizer.getTotalSize() -
        virtualItems[virtualItems.length - 1].end
      : 0;

  const tableClassNames = classNames(
    "data-table",
    { "data-table--dense": dense },
    className,
  );

  // Helper function to render table content
  const renderTableContent = useCallback(() => {
    if (isDataLoading) {
      return (
        <tr className="loading-row">
          <td colSpan={100} className="py-4">
            <div className="flex items-center justify-center">
              <LoadingIcon className="mr-2 text-sm" />
              <p>Loading data...</p>
            </div>
          </td>
        </tr>
      );
    }

    if (rows.length === 0) {
      return (
        <tr className="empty-row">
          <td colSpan={columns.length}>
            <p className="text-center">No data</p>
          </td>
        </tr>
      );
    }

    return (
      <>
        {paddingTop > 0 && (
          <tr className="virtual-row-spacer">
            <td
              style={{ height: `${paddingTop}px` }}
              colSpan={columns.length}
            />
          </tr>
        )}
        {virtualItems.map((virtualRow) => {
          const row = rows[virtualRow.index];
          return (
            <tr key={row.id} data-index={virtualRow.index}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          );
        })}
        {paddingBottom > 0 && (
          <tr className="virtual-row-spacer">
            <td
              style={{ height: `${paddingBottom}px` }}
              colSpan={columns.length}
            />
          </tr>
        )}
      </>
    );
  }, [
    isDataLoading,
    columns.length,
    paddingTop,
    virtualItems,
    paddingBottom,
    rows,
  ]);

  const renderTableHeader = useCallback(() => {
    return table.getHeaderGroups().map((headerGroup) => (
      <tr key={headerGroup.id}>
        {headerGroup.headers.map((header) => (
          <th
            key={header.id}
            className={header.column.getCanSort() ? "sortable" : ""}
            aria-sort={
              header.column.getIsSorted()
                ? header.column.getIsSorted() === "asc"
                  ? "ascending"
                  : "descending"
                : undefined
            }
            onClick={header.column.getToggleSortingHandler()}
          >
            {!header.isPlaceholder && (
              <div className="flex items-center gap-1">
                {flexRender(
                  header.column.columnDef.header,
                  header.getContext(),
                )}
                {header.column.getCanSort() && (
                  <span className="sort-indicator">
                    {header.column.getIsSorted() === "asc" ? (
                      <SortUpIcon />
                    ) : header.column.getIsSorted() === "desc" ? (
                      <SortDownIcon />
                    ) : (
                      <SortUpDownIcon />
                    )}
                  </span>
                )}
              </div>
            )}
          </th>
        ))}
      </tr>
    ));
  }, [table]);

  return (
    <div className="data-table-wrapper">
      <table className={tableClassNames}>
        <thead>{renderTableHeader()}</thead>
        <tbody ref={scrollParentRef} className="data-table-body">
          {renderTableContent()}
        </tbody>
      </table>
    </div>
  );
};
