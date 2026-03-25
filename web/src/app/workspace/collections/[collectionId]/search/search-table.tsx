'use client';

import { SearchResult } from '@/api';
import { DataGrid, DataGridPagination } from '@/components/data-grid';
import { FormatDate } from '@/components/format-date';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import {
  ColumnDef,
  ColumnFiltersState,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from '@tanstack/react-table';
import _ from 'lodash';
import {
  AlertTriangle,
  ChevronDown,
  Columns3,
  EllipsisVertical,
  Info,
  MessageSquareText,
  Trash,
} from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import * as React from 'react';
import {
  canUseLegacyGraphSearch,
  getQaEntryLabel,
  getQueryAccessCopy,
  type CollectionQueryAccess,
} from '../../tools';
import { SearchDelete } from './search-delete';
import { SearchResultDrawer } from './search-result-drawer';
import { SearchTest } from './search-test';

export const SearchTable = ({
  data,
  queryAccess,
}: {
  data: SearchResult[];
  queryAccess: CollectionQueryAccess;
}) => {
  const locale = useLocale();
  const { collection } = useCollectionContext();
  const page_search = useTranslations('page_search');
  const [rowSelection, setRowSelection] = React.useState({});
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({
      created: false,
    });
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );
  const [sorting, setSorting] = React.useState<SortingState>([
    {
      id: 'created',
      desc: true,
    },
  ]);
  const [pagination, setPagination] = React.useState({
    pageIndex: 0,
    pageSize: 20,
  });
  const [searchValue, setSearchValue] = React.useState('');

  const queryAccessCopy = React.useMemo(
    () => getQueryAccessCopy(queryAccess, locale),
    [locale, queryAccess],
  );
  const isBlocked = queryAccess.state === 'blocked';

  const columns: ColumnDef<SearchResult>[] = React.useMemo(() => {
    const indexCols: ColumnDef<SearchResult>[] = [];

    if (collection.config?.enable_vector) {
      indexCols.push({
        accessorKey: 'vector_search',
        header: page_search('vector_search'),
        cell: ({ row }) => {
          return (
            <div>
              <div>topk: {row.original.vector_search?.topk}</div>
              <div>similarity: {row.original.vector_search?.similarity}</div>
            </div>
          );
        },
      });
    }

    if (collection.config?.enable_fulltext) {
      indexCols.push({
        accessorKey: 'fulltext_search',
        header: page_search('fulltext_search'),
        cell: ({ row }) => {
          return (
            <div>
              <div>topk: {row.original.fulltext_search?.topk}</div>
              <div>
                keywords: {row.original.fulltext_search?.keywords?.join(',')}
              </div>
            </div>
          );
        },
      });
    }

    if (canUseLegacyGraphSearch(collection.config)) {
      indexCols.push({
        accessorKey: 'graph_search',
        header: page_search('graph_search'),
        cell: ({ row }) => {
          return <div>topk: {row.original.fulltext_search?.topk}</div>;
        },
      });
    }

    if (collection.config?.enable_summary) {
      indexCols.push({
        accessorKey: 'summary_search',
        header: page_search('summary_search'),
        cell: ({ row }) => {
          return (
            <div>
              <div>topk: {row.original.summary_search?.topk || '--'}</div>
              <div>
                similarity: {row.original.summary_search?.similarity || '--'}
              </div>
            </div>
          );
        },
      });
    }

    return [
      {
        id: 'select',
        header: ({ table }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={
                table.getIsAllPageRowsSelected() ||
                (table.getIsSomePageRowsSelected() && 'indeterminate')
              }
              onCheckedChange={(value) =>
                table.toggleAllPageRowsSelected(!!value)
              }
              aria-label="Select all"
            />
          </div>
        ),
        cell: ({ row }) => (
          <div className="flex items-center justify-center">
            <Checkbox
              checked={row.getIsSelected()}
              onCheckedChange={(value) => row.toggleSelected(!!value)}
              aria-label="Select row"
            />
          </div>
        ),
      },
      {
        accessorKey: 'query',
        header: page_search('questions'),
        cell: ({ row }) => {
          return (
            <div>
              <SearchResultDrawer result={row.original}>
                <div
                  data-result={!_.isEmpty(row.original.items)}
                  className="data-[result=true]:hover:text-primary max-w-md truncate data-[result=true]:cursor-pointer"
                >
                  {row.original.query}
                </div>
              </SearchResultDrawer>
              <div className="text-muted-foreground flex flex-row items-center gap-4">
                {_.size(row.original.items)} results
              </div>
            </div>
          );
        },
      },
      ...indexCols,
      {
        accessorKey: 'created',
        header: page_search('creation_time'),
        cell: ({ row }) => {
          return row.original.created ? (
            <FormatDate datetime={new Date(row.original.created)} />
          ) : undefined;
        },
      },
      {
        id: 'actions',
        enableHiding: false,
        cell: ({ row }) => (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="data-[state=open]:bg-muted text-muted-foreground flex size-8"
                size="icon"
              >
                <EllipsisVertical />
                <span className="sr-only">Open menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              <SearchDelete searchResult={row.original}>
                <DropdownMenuItem variant="destructive">
                  <Trash /> {page_search('delete')}
                </DropdownMenuItem>
              </SearchDelete>
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    ];
  }, [collection.config, page_search]);

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnVisibility,
      rowSelection,
      columnFilters,
      pagination,
      globalFilter: searchValue,
    },
    getRowId: (row) => String(row.id),
    enableRowSelection: true,
    onRowSelectionChange: setRowSelection,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
  });

  return (
    <div className="flex flex-col gap-4">
      {queryAccess.state !== 'ready' && (
        <Alert variant={isBlocked ? 'destructive' : 'default'}>
          {isBlocked ? <AlertTriangle /> : <Info />}
          <AlertTitle>{queryAccessCopy.badge}</AlertTitle>
          <AlertDescription>{queryAccessCopy.description}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="max-w-md flex-1">
          <Input
            placeholder={page_search('search')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.currentTarget.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <SearchTest disabled={isBlocked} queryAccess={queryAccess}>
            <Button disabled={isBlocked}>
              <MessageSquareText />
              <span className="hidden sm:inline">
                {getQaEntryLabel(locale)}
              </span>
            </Button>
          </SearchTest>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Columns3 />
                <ChevronDown />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              {table
                .getAllColumns()
                .filter(
                  (column) =>
                    typeof column.accessorFn !== 'undefined' &&
                    column.getCanHide(),
                )
                .map((column) => {
                  return (
                    <DropdownMenuCheckboxItem
                      key={column.id}
                      className="capitalize"
                      checked={column.getIsVisible()}
                      onCheckedChange={(value) =>
                        column.toggleVisibility(!!value)
                      }
                    >
                      {String(column.columnDef.header)}
                    </DropdownMenuCheckboxItem>
                  );
                })}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <DataGrid table={table} />
      <DataGridPagination table={table} />
    </div>
  );
};
