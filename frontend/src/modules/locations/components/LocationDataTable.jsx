import React, { useEffect, useMemo, useState } from 'react';
import { Trash2, Pencil } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Pagination from '../../../shared/components/Pagination';
import Table from '../../../shared/components/Table';
import { activeStatus, getRecordId } from '../utils';

const LocationDataTable = ({
    rows,
    columns,
    onEdit,
    onDelete,
    onBulkDelete,
    bulkLabel = 'records',
    loading = false,
    pageSize = 100,
}) => {
    const [selectedIds, setSelectedIds] = useState([]);
    const [page, setPage] = useState(1);

    const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
    const safePage = Math.min(page, totalPages);

    const pagedRows = useMemo(
        () => rows.slice((safePage - 1) * pageSize, safePage * pageSize),
        [rows, safePage, pageSize]
    );

    const selectedRows = useMemo(
        () => rows.filter((row) => selectedIds.includes(getRecordId(row))),
        [rows, selectedIds]
    );

    useEffect(() => {
        const timer = window.setTimeout(() => {
            setSelectedIds([]);
            setPage(1);
        }, 0);

        return () => window.clearTimeout(timer);
    }, [rows]);

    const actionColumn = onEdit || onDelete
        ? [
            {
                header: 'Actions',
                render: (row) => (
                    <div className="flex items-center gap-1">
                        {onEdit && (
                            <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => onEdit(row)}
                                title="Edit"
                            >
                                <Pencil size={15} />
                            </Button>
                        )}

                        {onDelete && (
                            <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => onDelete(row)}
                                title="Delete"
                            >
                                <Trash2 size={15} />
                            </Button>
                        )}
                    </div>
                ),
            },
        ]
        : [];

    return (
        <div className="space-y-3">
            {onBulkDelete && (
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border bg-background px-3 py-2">
                    <p className="text-sm text-text-secondary">
                        {selectedIds.length} selected
                    </p>

                    <div className="flex items-center gap-2">
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={!rows.length}
                            onClick={() =>
                                setSelectedIds([
                                    ...new Set([
                                        ...selectedIds,
                                        ...pagedRows.map(getRecordId).filter(Boolean),
                                    ]),
                                ])
                            }
                        >
                            Select Page
                        </Button>

                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            disabled={!selectedIds.length}
                            onClick={() => setSelectedIds([])}
                        >
                            Clear
                        </Button>

                        <Button
                            type="button"
                            variant="danger"
                            size="sm"
                            loading={loading}
                            disabled={!selectedIds.length}
                            onClick={() => onBulkDelete(selectedRows, bulkLabel)}
                            className="gap-2"
                        >
                            <Trash2 size={15} />
                            Delete Selected
                        </Button>
                    </div>
                </div>
            )}

            <Table
                data={pagedRows}
                selectable={Boolean(onBulkDelete)}
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                columns={[
                    ...columns,
                    {
                        header: 'Status',
                        render: (row) => (
                            <span
                                className={`rounded-md px-2 py-1 text-xs font-semibold ${
                                    row.is_active !== false
                                        ? 'bg-success/10 text-success'
                                        : 'bg-danger/10 text-danger'
                                }`}
                            >
                                {activeStatus(row)}
                            </span>
                        ),
                    },
                    ...actionColumn,
                ]}
            />

            <Pagination
                currentPage={safePage}
                totalPages={totalPages}
                totalCount={rows.length}
                pageSize={pageSize}
                onPageChange={setPage}
            />
        </div>
    );
};

export default LocationDataTable;
