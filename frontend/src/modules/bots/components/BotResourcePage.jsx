import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { botsAPI } from '../api';
import { formatLabel, getList } from '../utils';

const renderValue = (value) => {
    if (value === null || value === undefined || value === '') return '-';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return value.length ? value.join(', ') : '-';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
};

const BotResourcePage = ({ title, description, endpoint, columns = [], emptyText }) => {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadRows = useCallback(async () => {
        const loader = botsAPI[endpoint];
        if (!loader) {
            setError(`Missing API loader: ${endpoint}`);
            setLoading(false);
            return;
        }
        setLoading(true);
        setError('');
        try {
            const response = await loader({ all: true });
            setRows(getList(response));
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load records.');
        } finally {
            setLoading(false);
        }
    }, [endpoint]);

    useEffect(() => {
        loadRows();
    }, [loadRows]);

    const safeColumns = useMemo(() => {
        if (columns.length > 0) return columns;
        const sample = rows[0] || {};
        return Object.keys(sample).slice(0, 5).map((key) => ({ key, label: formatLabel(key) }));
    }, [columns, rows]);

    return (
        <div className="space-y-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">{title}</h1>
                    <p className="text-sm text-text-secondary">{description}</p>
                </div>
                <Button type="button" variant="secondary" className="gap-2" onClick={loadRows} loading={loading}>
                    <RefreshCw size={16} />
                    Refresh
                </Button>
            </div>

            <section className="overflow-hidden rounded-lg border border-border bg-card">
                <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
                    <h2 className="font-semibold text-text-primary">{title}</h2>
                    <span className="text-xs text-text-secondary">{loading ? 'Loading...' : `${rows.length} records`}</span>
                </div>

                {error ? (
                    <div className="p-4 text-sm text-danger">{error}</div>
                ) : rows.length === 0 ? (
                    <div className="p-6 text-sm text-text-secondary">{loading ? 'Loading records...' : emptyText || 'No records found.'}</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-border text-sm">
                            <thead className="bg-background">
                                <tr>
                                    {safeColumns.map((column) => (
                                        <th key={column.key} className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-text-secondary">
                                            {column.label}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {rows.map((row) => (
                                    <tr key={row.id} className="hover:bg-background/60">
                                        {safeColumns.map((column) => (
                                            <td key={column.key} className="max-w-[360px] px-4 py-3 text-text-primary">
                                                <span className="line-clamp-2 break-words">{renderValue(row[column.key])}</span>
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
};

export default BotResourcePage;
