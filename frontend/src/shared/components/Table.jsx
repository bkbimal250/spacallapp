import React from 'react';

const Table = ({
    columns,
    data,
    onRowClick,
    selectable = false,
    selectedIds = [],
    onSelectionChange
}) => {
    const allIds = data.map(row => row.id || row.ID);
    const isAllSelected = data.length > 0 && allIds.every(id => selectedIds.includes(id));

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            onSelectionChange(allIds);
        } else {
            onSelectionChange([]);
        }
    };

    const handleSelectRow = (e, id) => {
        e.stopPropagation();
        if (e.target.checked) {
            onSelectionChange([...selectedIds, id]);
        } else {
            onSelectionChange(selectedIds.filter(selectedId => selectedId !== id));
        }
    };

    return (
        <div className="flex flex-col">
            <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                    <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    {selectable && (
                                        <th scope="col" className="px-6 py-3 text-left">
                                            <input
                                                type="checkbox"
                                                className="h-4 w-4 text-sky-600 focus:ring-sky-500 border-gray-300 rounded"
                                                checked={isAllSelected}
                                                onChange={handleSelectAll}
                                            />
                                        </th>
                                    )}
                                    {columns.map((col, idx) => (
                                        <th
                                            key={idx}
                                            scope="col"
                                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                        >
                                            {col.header}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {data && Array.isArray(data) ? data.map((row, rowIndex) => {
                                    const rowId = row.id || row.ID;
                                    const isSelected = selectedIds.includes(rowId);

                                    return (
                                        <tr
                                            key={rowIndex}
                                            onClick={() => onRowClick && onRowClick(row)}
                                            className={`${onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''} ${isSelected ? 'bg-sky-50' : ''}`}
                                        >
                                            {selectable && (
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <input
                                                        type="checkbox"
                                                        className="h-4 w-4 text-sky-600 focus:ring-sky-500 border-gray-300 rounded"
                                                        checked={isSelected}
                                                        onChange={(e) => handleSelectRow(e, rowId)}
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                </td>
                                            )}
                                            {columns.map((col, colIndex) => (
                                                <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {col.render ? col.render(row) : row[col.accessor]}
                                                </td>
                                            ))}
                                        </tr>
                                    );
                                }) : (
                                    <tr>
                                        <td colSpan={selectable ? columns.length + 1 : columns.length} className="px-6 py-4 text-center text-sm text-gray-500">
                                            No data available
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Table;
