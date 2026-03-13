import React, { useMemo, memo } from 'react';

const Table = memo(({
    columns,
    data = [],
    onRowClick,
    selectable = false,
    selectedIds = [],
    onSelectionChange
}) => {

    const allIds = useMemo(() => data.map(row => row.id || row.ID), [data]);
    
    // Use a Set for O(1) lookups
    const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);

    const isAllSelected = useMemo(() => 
        data.length > 0 && allIds.every(id => selectedSet.has(id)),
    [data, allIds, selectedSet]);

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            onSelectionChange([...allIds]);
        } else {
            onSelectionChange([]);
        }
    };

    const handleSelectRow = (e, id) => {
        e.stopPropagation();
        if (e.target.checked) {
            onSelectionChange([...selectedIds, id]);
        } else {
            onSelectionChange(
                selectedIds.filter(selectedId => selectedId !== id)
            );
        }
    };

    return (
        <div className="w-full overflow-x-auto">
            <table className="min-w-full border border-border rounded-lg overflow-hidden">
                {/* HEADER */}
                <thead className="bg-card border-b border-border">
                    <tr>
                        {selectable && (
                            <th className="px-4 py-3 text-left w-10">
                                <input
                                    type="checkbox"
                                    className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary cursor-pointer"
                                    checked={isAllSelected}
                                    onChange={handleSelectAll}
                                />
                            </th>
                        )}
                        {columns.map((col, idx) => (
                            <th
                                key={idx}
                                className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider"
                            >
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>

                {/* BODY */}
                <tbody className="bg-background divide-y divide-border">
                    {data && data.length > 0 ? (
                        data.map((row, rowIndex) => {
                            const rowId = row.id || row.ID;
                            const isSelected = selectedSet.has(rowId);

                            return (
                                <tr
                                    key={rowId || rowIndex}
                                    onClick={() => onRowClick && onRowClick(row)}
                                    className={`transition duration-150 ${onRowClick
                                        ? 'cursor-pointer hover:bg-background/70'
                                        : ''
                                        } ${isSelected ? 'bg-primary/10' : ''}`}
                                >
                                    {selectable && (
                                        <td className="px-4 py-3">
                                            <input
                                                type="checkbox"
                                                className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary cursor-pointer"
                                                checked={isSelected}
                                                onChange={(e) => handleSelectRow(e, rowId)}
                                                onClick={(e) => e.stopPropagation()}
                                            />
                                        </td>
                                    )}
                                    {columns.map((col, colIndex) => (
                                        <td
                                            key={colIndex}
                                            className="px-4 py-3 text-sm text-text-primary"
                                        >
                                            {col.render
                                                ? col.render(row)
                                                : row[col.accessor]}
                                        </td>
                                    ))}
                                </tr>
                            );
                        })
                    ) : (
                        <tr>
                            <td
                                colSpan={selectable ? columns.length + 1 : columns.length}
                                className="px-4 py-10 text-center text-sm text-text-secondary italic"
                            >
                                No data available
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
});

export default Table;