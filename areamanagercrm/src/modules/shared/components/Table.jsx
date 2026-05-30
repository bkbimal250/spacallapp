import React, { useMemo, memo } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react';

const Table = memo(({
    columns,
    data = [],
    onRowClick,
    selectable = false,
    selectedIds = [],
    onSelectionChange,
    onSort,
    sortConfig = { key: null, direction: 'asc' }
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
                        {columns.map((col, idx) => {
                            const isSortable = !!col.sortKey && !!onSort;
                            const isActive = sortConfig.key === col.sortKey;

                            return (
                                <th
                                    key={idx}
                                    className={`px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider ${isSortable ? 'cursor-pointer hover:text-primary transition-colors group' : ''}`}
                                    onClick={() => isSortable && onSort(col.sortKey)}
                                    title={
                                        isSortable
                                            ? isActive
                                                ? `Currently sorted ${sortConfig.direction === 'asc' ? 'A to Z / Smallest first' : 'Z to A / Largest first'}. Click to flip order.`
                                                : `Sort by ${col.header}`
                                            : undefined
                                    }
                                >
                                    <div className="flex items-center gap-1.5">
                                        <span>{col.header}</span>
                                        {isSortable && (
                                            <div 
                                                className="flex-shrink-0"
                                                title={isActive 
                                                    ? (sortConfig.direction === 'asc' ? 'Sorting Ascending' : 'Sorting Descending') 
                                                    : 'Click to sort this column'
                                                }
                                            >
                                                {isActive ? (
                                                    sortConfig.direction === 'asc' ? (
                                                        <ArrowUp size={14} className="text-primary animate-in fade-in zoom-in duration-300" />
                                                    ) : (
                                                        <ArrowDown size={14} className="text-primary animate-in fade-in zoom-in duration-300" />
                                                    )
                                                ) : (
                                                    <ArrowUpDown size={14} className="opacity-10 group-hover:opacity-50 transition-opacity" />
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </th>
                            );
                        })}
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