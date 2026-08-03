import React, { useEffect, useMemo, useState } from 'react';
import { monitoringAPI } from '../api';

const fmtMs = (value) => `${Number(value || 0).toFixed(0)}ms`;

const StatusPill = ({ ok }) => (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${ok ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
        {ok ? 'OK' : 'Check'}
    </span>
);

const MetricCard = ({ label, value, sub }) => (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-textSecondary">{label}</p>
        <p className="mt-2 text-2xl font-bold text-textPrimary">{value}</p>
        {sub && <p className="mt-1 text-xs text-textMuted">{sub}</p>}
    </div>
);

const MonitoringDashboard = () => {
    const [minutes, setMinutes] = useState(60);
    const [summary, setSummary] = useState([]);
    const [requests, setRequests] = useState([]);
    const [slowQueries, setSlowQueries] = useState([]);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const totals = useMemo(() => {
        const requestCount = summary.reduce((sum, row) => sum + Number(row.request_count || 0), 0);
        const errorCount = summary.reduce((sum, row) => sum + Number(row.error_count || 0), 0);
        const avgMs = summary.length
            ? summary.reduce((sum, row) => sum + Number(row.avg_ms || 0), 0) / summary.length
            : 0;
        const cacheHitRate = summary.length
            ? summary.reduce((sum, row) => sum + Number(row.cache_hit_rate || 0), 0) / summary.length
            : 0;
        return { requestCount, errorCount, avgMs, cacheHitRate };
    }, [summary]);

    const load = async () => {
        setLoading(true);
        setError('');
        try {
            const [summaryRes, requestsRes, slowRes, healthRes] = await Promise.all([
                monitoringAPI.summary(minutes),
                monitoringAPI.requests(25),
                monitoringAPI.slowQueries(25),
                monitoringAPI.health(),
            ]);
            setSummary(summaryRes.data?.endpoints || []);
            setRequests(requestsRes.data || []);
            setSlowQueries(slowRes.data || []);
            setHealth(healthRes.data || null);
        } catch (err) {
            setError(err.response?.status >= 500 ? 'Monitoring data is temporarily unavailable.' : 'Unable to load monitoring data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        const timer = window.setInterval(load, 30000);
        return () => window.clearInterval(timer);
    }, [minutes]);

    return (
        <div className="space-y-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-xl font-bold text-textPrimary">Monitoring</h1>
                    <p className="text-sm text-textSecondary">Dashboard API latency, SQL pressure, cache behavior, and health.</p>
                </div>
                <div className="flex items-center gap-2">
                    {[15, 60, 240].map((value) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => setMinutes(value)}
                            className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                                minutes === value
                                    ? 'border-primary bg-primary text-white'
                                    : 'border-border bg-card text-textSecondary hover:text-textPrimary'
                            }`}
                        >
                            {value < 60 ? `${value}m` : `${value / 60}h`}
                        </button>
                    ))}
                    <button
                        type="button"
                        onClick={load}
                        className="rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold text-textSecondary hover:text-textPrimary"
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {error && <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                <MetricCard label="Requests" value={totals.requestCount} sub={`Last ${minutes} minutes`} />
                <MetricCard label="Average" value={fmtMs(totals.avgMs)} sub="Across observed endpoints" />
                <MetricCard label="Cache Hit" value={`${totals.cacheHitRate.toFixed(1)}%`} sub="Dashboard cache" />
                <MetricCard label="Errors" value={totals.errorCount} sub="HTTP 500+" />
                <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold uppercase tracking-wide text-textSecondary">Health</p>
                        <StatusPill ok={health?.status === 'ok'} />
                    </div>
                    <div className="mt-3 space-y-2 text-sm text-textSecondary">
                        <div className="flex justify-between"><span>Database</span><span>{fmtMs(health?.checks?.database?.latency_ms)}</span></div>
                        <div className="flex justify-between"><span>Cache</span><span>{fmtMs(health?.checks?.cache?.latency_ms)}</span></div>
                    </div>
                </div>
            </div>

            <section className="rounded-xl border border-border bg-card shadow-sm">
                <div className="border-b border-border px-4 py-3">
                    <h2 className="text-sm font-bold text-textPrimary">Endpoint Performance</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                        <thead className="bg-background text-xs uppercase text-textSecondary">
                            <tr>
                                <th className="px-4 py-3 text-left">Endpoint</th>
                                <th className="px-4 py-3 text-right">Requests</th>
                                <th className="px-4 py-3 text-right">Avg</th>
                                <th className="px-4 py-3 text-right">Max</th>
                                <th className="px-4 py-3 text-right">SQL</th>
                                <th className="px-4 py-3 text-right">Cache</th>
                                <th className="px-4 py-3 text-right">Errors</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {(loading && !summary.length ? [] : summary).map((row) => (
                                <tr key={row.path}>
                                    <td className="max-w-[360px] truncate px-4 py-3 font-medium text-textPrimary">{row.path}</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{row.request_count}</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{fmtMs(row.avg_ms)}</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{fmtMs(row.max_ms)}</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{Number(row.avg_sql || 0).toFixed(1)}</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{Number(row.cache_hit_rate || 0).toFixed(1)}%</td>
                                    <td className="px-4 py-3 text-right text-textSecondary">{row.error_count}</td>
                                </tr>
                            ))}
                            {!loading && !summary.length && (
                                <tr><td colSpan="7" className="px-4 py-8 text-center text-textMuted">No observed dashboard requests yet.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </section>

            <div className="grid gap-5 xl:grid-cols-2">
                <section className="rounded-xl border border-border bg-card shadow-sm">
                    <div className="border-b border-border px-4 py-3">
                        <h2 className="text-sm font-bold text-textPrimary">Recent Requests</h2>
                    </div>
                    <div className="divide-y divide-border">
                        {requests.map((row) => (
                            <div key={`${row.request_id}-${row.created_at}`} className="px-4 py-3">
                                <div className="flex items-center justify-between gap-3">
                                    <p className="truncate text-sm font-semibold text-textPrimary">{row.path}</p>
                                    <span className="shrink-0 text-sm font-bold text-textSecondary">{fmtMs(row.duration_ms)}</span>
                                </div>
                                <p className="mt-1 truncate text-xs text-textMuted">{row.request_id} · SQL {row.sql_count} · HTTP {row.status_code}</p>
                            </div>
                        ))}
                        {!requests.length && <div className="px-4 py-8 text-center text-sm text-textMuted">No recent requests.</div>}
                    </div>
                </section>

                <section className="rounded-xl border border-border bg-card shadow-sm">
                    <div className="border-b border-border px-4 py-3">
                        <h2 className="text-sm font-bold text-textPrimary">Slow Queries</h2>
                    </div>
                    <div className="divide-y divide-border">
                        {slowQueries.map((row) => (
                            <div key={`${row.request_id}-${row.created_at}`} className="px-4 py-3">
                                <div className="flex items-center justify-between gap-3">
                                    <p className="truncate text-sm font-semibold text-textPrimary">{row.path}</p>
                                    <span className="shrink-0 text-sm font-bold text-danger">{fmtMs(row.duration_ms)}</span>
                                </div>
                                <p className="mt-1 line-clamp-2 text-xs text-textMuted">{row.sql}</p>
                            </div>
                        ))}
                        {!slowQueries.length && <div className="px-4 py-8 text-center text-sm text-textMuted">No slow queries captured.</div>}
                    </div>
                </section>
            </div>
        </div>
    );
};

export default MonitoringDashboard;
