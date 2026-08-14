import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { AlertTriangle, BarChart3, Eye, FileText, GitBranch, RefreshCw, Search, SlidersHorizontal, Trash2, X } from 'lucide-react';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Pagination from '../../../shared/components/Pagination';
import { callRoutingAPI } from '../api';

const PAGE_SIZE = 20;

const requestStatuses = ['', 'pending', 'processing', 'routed', 'skipped', 'failed'];
const whatsappStatuses = ['', 'pending', 'queued', 'sending', 'sent', 'delivered', 'read', 'failed', 'cancelled'];

const badgeVariant = {
    routed: 'success',
    delivered: 'success',
    read: 'success',
    skipped: 'warning',
    queued: 'info',
    sending: 'info',
    sent: 'info',
    processing: 'info',
    pending: 'gray',
    failed: 'danger',
    cancelled: 'warning',
};

const labelize = (value) => (value ? String(value).replace(/_/g, ' ') : 'None');
const formatDate = (value) => (value ? new Date(value).toLocaleString('en-IN') : 'N/A');
const compactId = (value) => (value ? String(value).slice(0, 8) : '');

const StatusBadge = ({ value }) => (
    <Badge variant={badgeVariant[value] || 'gray'} className="capitalize whitespace-nowrap">
        {labelize(value || 'none')}
    </Badge>
);

const CallRouting = () => {
    const { user } = useSelector((state) => state.auth);
    const [activeTab, setActiveTab] = useState('requests');
    const [requests, setRequests] = useState([]);
    const [rules, setRules] = useState([]);
    const [summary, setSummary] = useState(null);
    const [integrationStatus, setIntegrationStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [deletingId, setDeletingId] = useState('');
    const [selectedRequest, setSelectedRequest] = useState(null);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [searchDraft, setSearchDraft] = useState('');
    const [filters, setFilters] = useState({
        search: '',
        date_from: '',
        date_to: '',
        status: '',
        source_branch_search: '',
        city: '',
        area: '',
        routing_rule: '',
        whatsapp_status: '',
    });

    const params = useMemo(() => {
        const clean = { page, page_size: PAGE_SIZE };
        Object.entries(filters).forEach(([key, value]) => {
            if (value) clean[key] = value;
        });
        return clean;
    }, [filters, page]);

    const normalizedRole = String(user?.role || '').toLowerCase();
    const canDelete = normalizedRole === 'admin' || normalizedRole === 'super_admin';

    const fetchRequests = useCallback(async () => {
        setLoading(true);
        try {
            const [requestResponse, summaryResponse] = await Promise.all([
                callRoutingAPI.getRequests(params),
                callRoutingAPI.getSummary(params),
            ]);
            setRequests(requestResponse.data?.results || []);
            setTotalCount(requestResponse.data?.count || 0);
            setSummary(summaryResponse.data || null);
        } catch (error) {
            console.error('Failed to fetch call routing requests', error);
            setRequests([]);
            setTotalCount(0);
        } finally {
            setLoading(false);
        }
    }, [params]);

    const fetchRules = useCallback(async () => {
        try {
            const response = await callRoutingAPI.getRules({ page_size: 100 });
            setRules(response.data?.results || response.data || []);
        } catch (error) {
            console.error('Failed to fetch routing rules', error);
            setRules([]);
        }
    }, []);

    const fetchIntegrationStatus = useCallback(async () => {
        try {
            const response = await callRoutingAPI.getIntegrationStatus();
            setIntegrationStatus(response.data || null);
        } catch (error) {
            console.error('Failed to fetch call routing integration status', error);
            setIntegrationStatus(null);
        }
    }, []);

    useEffect(() => {
        const timeout = window.setTimeout(() => {
            setPage(1);
            setFilters((current) => ({ ...current, search: searchDraft.trim() }));
        }, 350);
        return () => window.clearTimeout(timeout);
    }, [searchDraft]);

    useEffect(() => {
        fetchRequests();
    }, [fetchRequests]);

    useEffect(() => {
        fetchRules();
        fetchIntegrationStatus();
    }, [fetchRules, fetchIntegrationStatus]);

    const updateFilter = (key, value) => {
        setPage(1);
        setFilters((current) => ({ ...current, [key]: value }));
    };

    const resetFilters = () => {
        setSearchDraft('');
        setPage(1);
        setFilters({
            search: '',
            date_from: '',
            date_to: '',
            status: '',
            source_branch_search: '',
            city: '',
            area: '',
            routing_rule: '',
            whatsapp_status: '',
        });
    };

    const openRequest = async (id) => {
        setDetailLoading(true);
        try {
            const response = await callRoutingAPI.getRequest(id);
            setSelectedRequest(response.data);
        } catch (error) {
            console.error('Failed to fetch routing request detail', error);
        } finally {
            setDetailLoading(false);
        }
    };

    const deleteRequest = async (request) => {
        if (!canDelete || !request?.id) return;
        const confirmed = window.confirm(`Delete routing request ${compactId(request.id)}? This removes routing audit records only and keeps the original CallLog/Lead.`);
        if (!confirmed) return;
        setDeletingId(request.id);
        try {
            await callRoutingAPI.deleteRequest(request.id);
            if (selectedRequest?.id === request.id) {
                setSelectedRequest(null);
            }
            await fetchRequests();
        } catch (error) {
            console.error('Failed to delete routing request', error);
            window.alert('Delete failed. Check permissions and try again.');
        } finally {
            setDeletingId('');
        }
    };

    const totalPages = Math.ceil(totalCount / PAGE_SIZE);

    return (
        <div className="space-y-5">
            <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Call Routing</h1>
                    <p className="text-sm text-text-secondary">Routing audit, recommendations and WhatsApp preparation status from backend records.</p>
                </div>
                <Button variant="secondary" className="gap-2" onClick={fetchRequests} loading={loading}>
                    <RefreshCw size={16} />
                    Refresh
                </Button>
            </div>

            <div className="flex flex-wrap gap-1 rounded-lg border border-border bg-card p-1">
                {[
                    { key: 'overview', label: 'Overview', icon: BarChart3 },
                    { key: 'requests', label: 'Routing Requests', icon: GitBranch },
                    { key: 'rules', label: 'Routing Rules', icon: FileText },
                    { key: 'analytics', label: 'Analytics', icon: SlidersHorizontal },
                ].map((tab) => (
                    <button
                        key={tab.key}
                        type="button"
                        onClick={() => setActiveTab(tab.key)}
                        className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                            activeTab === tab.key ? 'bg-primary text-white' : 'text-text-secondary hover:bg-background hover:text-text-primary'
                        }`}
                    >
                        {React.createElement(tab.icon, { size: 16 })}
                        {tab.label}
                    </button>
                ))}
            </div>

            {(activeTab === 'overview' || activeTab === 'requests' || activeTab === 'analytics') && (
                <SummaryGrid summary={summary} loading={loading} />
            )}

            {(activeTab === 'overview' || activeTab === 'requests') && (
                <IntegrationStatusPanel status={integrationStatus} />
            )}

            {activeTab === 'requests' && (
                <>
                    <RequestFilters
                        filters={filters}
                        rules={rules}
                        searchDraft={searchDraft}
                        setSearchDraft={setSearchDraft}
                        updateFilter={updateFilter}
                        resetFilters={resetFilters}
                    />
                    <RequestTable rows={requests} loading={loading} onOpen={openRequest} onDelete={deleteRequest} canDelete={canDelete} deletingId={deletingId} />
                    <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} totalCount={totalCount} pageSize={PAGE_SIZE} />
                </>
            )}

            {activeTab === 'rules' && <RulesTable rules={rules} />}
            {activeTab === 'analytics' && <AnalyticsPanel summary={summary} />}

            {selectedRequest && (
                <RequestDetailDrawer request={selectedRequest} loading={detailLoading} onClose={() => setSelectedRequest(null)} onDelete={deleteRequest} canDelete={canDelete} deletingId={deletingId} />
            )}
        </div>
    );
};

const SummaryGrid = ({ summary, loading }) => {
    const cards = [
        ['Total', summary?.total],
        ['Routed', summary?.routed],
        ['Skipped', summary?.skipped],
        ['Failed', summary?.failed],
        ['WhatsApp Queued', summary?.whatsapp_queued],
        ['Delivered', summary?.whatsapp_delivered],
        ['Routing Success', `${summary?.routing_success_rate || 0}%`],
        ['Delivery Rate', `${summary?.whatsapp_delivery_rate || 0}%`],
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">
            {cards.map(([label, value]) => (
                <div key={label} className="rounded-lg border border-border bg-card p-4">
                    <p className="text-xs font-medium uppercase text-text-secondary">{label}</p>
                    <p className="mt-2 text-2xl font-semibold text-text-primary">{loading ? '-' : value ?? 0}</p>
                </div>
            ))}
        </div>
    );
};

const IntegrationStatusPanel = ({ status }) => {
    const items = [
        ['Provider', status?.provider || 'DoubleTick'],
        ['Template', status?.template_name || 'night_spa_recommendation'],
        ['Language', status?.template_language_label || 'English'],
        ['Endpoint', status?.endpoint || '/whatsapp/message/template'],
        ['API Key', status?.api_key_configured ? 'Configured' : 'Missing'],
        ['WABA Sender', status?.waba_sender_configured ? 'Configured' : 'Missing'],
        ['Routing', status?.enable_call_routing ? 'Enabled' : 'Disabled'],
        ['WhatsApp Send', status?.enable_call_routing_whatsapp && !status?.call_routing_dry_run ? 'Live' : 'Safe / Dry Run'],
    ];

    return (
        <div className="rounded-lg border border-border bg-card p-4">
            <div className="mb-3 flex items-center gap-2">
                <AlertTriangle size={16} className={status?.api_key_configured && status?.waba_sender_configured ? 'text-success' : 'text-warning'} />
                <h2 className="text-sm font-semibold uppercase text-text-secondary">Integration Status</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-8">
                {items.map(([label, value]) => (
                    <div key={label} className="rounded-lg bg-background p-3">
                        <p className="text-xs text-text-secondary">{label}</p>
                        <p className="mt-1 break-words text-sm font-medium text-text-primary">{value}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

const RequestFilters = ({ filters, rules, searchDraft, setSearchDraft, updateFilter, resetFilters }) => (
    <div className="rounded-lg border border-border bg-card p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
            <Input label="Search" value={searchDraft} onChange={(event) => setSearchDraft(event.target.value)} placeholder="Customer, phone, spa, call ID" />
            <Input label="From" type="date" value={filters.date_from} onChange={(event) => updateFilter('date_from', event.target.value)} />
            <Input label="To" type="date" value={filters.date_to} onChange={(event) => updateFilter('date_to', event.target.value)} />
            <Select label="Routing Status" value={filters.status} onChange={(value) => updateFilter('status', value)} options={requestStatuses} />
            <Select label="WhatsApp Status" value={filters.whatsapp_status} onChange={(value) => updateFilter('whatsapp_status', value)} options={whatsappStatuses} />
            <Input label="Source Spa" value={filters.source_branch_search} onChange={(event) => updateFilter('source_branch_search', event.target.value)} />
            <Input label="City" value={filters.city} onChange={(event) => updateFilter('city', event.target.value)} />
            <Input label="Area" value={filters.area} onChange={(event) => updateFilter('area', event.target.value)} />
            <Select
                label="Routing Rule"
                value={filters.routing_rule}
                onChange={(value) => updateFilter('routing_rule', value)}
                options={['', ...rules.map((rule) => rule.id)]}
                labels={Object.fromEntries(rules.map((rule) => [rule.id, rule.name]))}
            />
            <div className="flex items-end">
                <Button variant="ghost" className="w-full gap-2" onClick={resetFilters}>
                    <Search size={16} />
                    Clear Filters
                </Button>
            </div>
        </div>
    </div>
);

const Select = ({ label, value, options, labels = {}, onChange }) => (
    <label className="block">
        <span className="mb-1 block text-sm font-medium text-text-secondary">{label}</span>
        <select
            value={value}
            onChange={(event) => onChange(event.target.value)}
            className="block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary transition focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
        >
            {options.map((option) => (
                <option key={option || 'all'} value={option}>
                    {option ? labels[option] || labelize(option) : 'All'}
                </option>
            ))}
        </select>
    </label>
);

const RequestTable = ({ rows, loading, onOpen, onDelete, canDelete, deletingId }) => (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-sm">
                <thead className="bg-background">
                    <tr className="text-left text-xs font-semibold uppercase text-text-secondary">
                        {['Date & Time', 'Customer', 'Phone', 'Original Spa', 'Location', 'Source Status', 'Routing Rule', 'Routing Status', 'Selected Spas', 'WhatsApp', 'Actions'].map((head) => (
                            <th key={head} className="px-4 py-3 whitespace-nowrap">{head}</th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-border">
                    {loading && (
                        <tr><td className="px-4 py-8 text-center text-text-secondary" colSpan={11}>Loading routing requests...</td></tr>
                    )}
                    {!loading && rows.length === 0 && (
                        <tr><td className="px-4 py-8 text-center text-text-secondary" colSpan={11}>No routing requests found.</td></tr>
                    )}
                    {!loading && rows.map((row) => (
                        <tr key={row.id} className="hover:bg-background/60">
                            <td className="px-4 py-3 whitespace-nowrap">{formatDate(row.call_time || row.created_at)}</td>
                            <td className="px-4 py-3 font-medium text-text-primary">{row.customer_name}</td>
                            <td className="px-4 py-3 whitespace-nowrap">{row.phone_masked || 'N/A'}</td>
                            <td className="px-4 py-3 min-w-40">{row.original_spa || 'N/A'}</td>
                            <td className="px-4 py-3">{row.location || 'N/A'}</td>
                            <td className="px-4 py-3">{row.source_branch_open === null ? 'Unknown' : row.source_branch_open ? 'Open' : 'Closed'}</td>
                            <td className="px-4 py-3">{row.routing_rule_name || 'None'}</td>
                            <td className="px-4 py-3"><StatusBadge value={row.status} /></td>
                            <td className="px-4 py-3 min-w-48">{(row.selected_spas || []).map((spa) => spa.name).join(', ') || 'None'}</td>
                            <td className="px-4 py-3"><StatusBadge value={row.whatsapp_status} /></td>
                            <td className="px-4 py-3">
                                <div className="flex flex-wrap gap-2">
                                <Button variant="ghost" size="sm" className="gap-2" onClick={() => onOpen(row.id)}>
                                    <Eye size={15} />
                                    View
                                </Button>
                                <Button
                                    variant="danger"
                                    size="sm"
                                    className="gap-2"
                                    onClick={() => onDelete(row)}
                                    loading={deletingId === row.id}
                                    disabled={!canDelete}
                                    title={canDelete ? 'Delete routing request' : 'Only admin and super admin can delete'}
                                >
                                    <Trash2 size={15} />
                                    Delete
                                </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);

const RulesTable = ({ rules }) => (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
        <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-background text-left text-xs font-semibold uppercase text-text-secondary">
                <tr>{['Name', 'Type', 'Enabled', 'Window', 'Max Spas', 'Cooldown', 'WhatsApp', 'Template'].map((head) => <th key={head} className="px-4 py-3">{head}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-border">
                {rules.map((rule) => (
                    <tr key={rule.id}>
                        <td className="px-4 py-3 font-medium">{rule.name}</td>
                        <td className="px-4 py-3 capitalize">{labelize(rule.routing_type)}</td>
                        <td className="px-4 py-3"><StatusBadge value={rule.enabled ? 'routed' : 'cancelled'} /></td>
                        <td className="px-4 py-3">{rule.start_time || 'Any'} to {rule.end_time || 'Any'}</td>
                        <td className="px-4 py-3">{rule.max_recommendations}</td>
                        <td className="px-4 py-3">{rule.cooldown_minutes} min</td>
                        <td className="px-4 py-3">{rule.whatsapp_enabled ? 'Enabled' : 'Disabled'}</td>
                        <td className="px-4 py-3">{rule.template_name || 'Not configured'}</td>
                    </tr>
                ))}
                {rules.length === 0 && <tr><td colSpan={8} className="px-4 py-8 text-center text-text-secondary">No routing rules found.</td></tr>}
            </tbody>
        </table>
    </div>
);

const AnalyticsPanel = ({ summary }) => (
    <div className="rounded-lg border border-border bg-card p-5">
        <h2 className="text-lg font-semibold text-text-primary">Analytics</h2>
        <p className="mt-1 text-sm text-text-secondary">Only backend summary metrics are available in this phase. No synthetic charts are shown.</p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <MetricLine label="Routed Requests" value={summary?.routed || 0} />
            <MetricLine label="Skipped Requests" value={summary?.skipped || 0} />
            <MetricLine label="WhatsApp Failures" value={summary?.whatsapp_failed || 0} />
        </div>
    </div>
);

const MetricLine = ({ label, value }) => (
    <div className="rounded-lg border border-border bg-background p-4">
        <p className="text-text-secondary">{label}</p>
        <p className="mt-1 text-xl font-semibold text-text-primary">{value}</p>
    </div>
);

const RequestDetailDrawer = ({ request, onClose, onDelete, canDelete, deletingId }) => (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40">
        <aside className="h-full w-full max-w-5xl overflow-y-auto bg-background shadow-xl">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background px-5 py-4">
                <div>
                    <h2 className="text-lg font-semibold text-text-primary">Routing Request {compactId(request.id)}</h2>
                    <p className="text-sm text-text-secondary">{formatDate(request.call_time || request.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                    {canDelete && (
                        <Button variant="danger" size="sm" className="gap-2" onClick={() => onDelete(request)} loading={deletingId === request.id}>
                            <Trash2 size={16} />
                            Delete
                        </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close detail">
                        <X size={18} />
                    </Button>
                </div>
            </div>
            <div className="space-y-4 p-5">
                <DetailSection title="Customer & Original Enquiry">
                    <InfoGrid items={[
                        ['Routing Request ID', request.id],
                        ['CallLog ID', request.call_log_id],
                        ['Lead ID', request.lead_id],
                        ['Customer', request.customer_name],
                        ['Phone', request.phone_masked],
                        ['Call Type', request.call_log?.call_type],
                        ['Duration', `${request.call_log?.duration || 0}s`],
                        ['SIM Slot', request.call_log?.sim_slot],
                        ['Device', request.call_log?.phone_name || request.call_log?.device_uid],
                        ['Device ID', request.call_log?.device_id],
                        ['Device UID', request.call_log?.device_uid],
                        ['Lead Status', request.lead?.status || 'No lead'],
                        ['Lead Booking Date', request.lead?.booking_date],
                    ]} />
                </DetailSection>
                <DetailSection title="Source Spa & Routing Decision">
                    <InfoGrid items={[
                        ['Source Branch ID', request.source_branch_id],
                        ['Source Spa', request.source_branch?.spa_name],
                        ['Source Code', request.source_branch?.code],
                        ['Location', request.location],
                        ['Source Status', request.source_branch_open === null ? 'Unknown' : request.source_branch_open ? 'Open' : 'Closed'],
                        ['Open Checked At', formatDate(request.source_open_checked_at)],
                        ['Routing Rule ID', request.routing_rule_id],
                        ['Routing Rule', request.routing_rule?.name || 'None'],
                        ['Routing Type', labelize(request.routing_type)],
                        ['Routing Status', labelize(request.status)],
                        ['Rejection Reason', labelize(request.rejection_reason)],
                        ['Created At', formatDate(request.created_at)],
                        ['Updated At', formatDate(request.updated_at)],
                        ['Completed At', formatDate(request.completed_at)],
                    ]} />
                </DetailSection>
                <CandidateList title="Selected Spas" candidates={(request.candidates || []).filter((candidate) => candidate.is_selected)} />
                <CandidateList title="All Candidates" candidates={request.candidates || []} />
                <Timeline events={request.events || []} attempts={request.attempts || []} />
                <WhatsAppPanel messages={request.whatsapp_messages || []} />
            </div>
        </aside>
    </div>
);

const DetailSection = ({ title, children }) => (
    <section className="rounded-lg border border-border bg-card p-4">
        <h3 className="mb-3 text-sm font-semibold uppercase text-text-secondary">{title}</h3>
        {children}
    </section>
);

const InfoGrid = ({ items }) => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {items.map(([label, value]) => (
            <div key={label} className="rounded-lg bg-background p-3">
                <p className="text-xs text-text-secondary">{label}</p>
                <p className="mt-1 text-sm font-medium text-text-primary break-words">{value || 'N/A'}</p>
            </div>
        ))}
    </div>
);

const CandidateList = ({ title, candidates }) => (
    <DetailSection title={title}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {candidates.map((candidate) => (
                <div key={candidate.id} className="rounded-lg border border-border bg-background p-3">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <p className="font-medium text-text-primary">{candidate.branch?.spa_name}</p>
                            <p className="text-sm text-text-secondary">{[candidate.branch?.area, candidate.branch?.city].filter(Boolean).join(', ')}</p>
                        </div>
                        <StatusBadge value={candidate.is_selected ? 'routed' : candidate.is_eligible ? 'queued' : 'skipped'} />
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-text-secondary">
                        <span>Rank {candidate.rank || '-'}</span>
                        <span>Score {candidate.relevance_score}</span>
                        <span>{candidate.is_open ? 'Open' : 'Closed'}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-text-secondary">
                        <span>Eligible: {candidate.is_eligible ? 'Yes' : 'No'}</span>
                        <span>Selected: {candidate.is_selected ? 'Yes' : 'No'}</span>
                        <span>Branch ID: {compactId(candidate.branch?.id)}</span>
                        <span>Phone: {candidate.branch?.phone || 'N/A'}</span>
                    </div>
                    {candidate.rejection_reason && <p className="mt-2 text-xs text-danger">{candidate.rejection_reason}</p>}
                    {candidate.metadata && Object.keys(candidate.metadata).length > 0 && (
                        <pre className="mt-2 max-h-32 overflow-auto rounded border border-border bg-card p-2 text-xs">
                            {JSON.stringify(candidate.metadata, null, 2)}
                        </pre>
                    )}
                </div>
            ))}
            {candidates.length === 0 && <p className="text-sm text-text-secondary">No candidates recorded.</p>}
        </div>
    </DetailSection>
);

const Timeline = ({ events, attempts }) => (
    <DetailSection title="Timeline & Attempts">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="space-y-2">
                {events.map((event) => (
                    <div key={event.id} className="rounded-lg bg-background p-3">
                        <p className="text-sm font-medium capitalize">{labelize(event.event_type)}</p>
                        <p className="text-xs text-text-secondary">{formatDate(event.created_at)}</p>
                        {event.message && <p className="mt-1 text-sm text-text-secondary">{event.message}</p>}
                    </div>
                ))}
                {events.length === 0 && <p className="text-sm text-text-secondary">No events recorded.</p>}
            </div>
            <div className="space-y-2">
                {attempts.map((attempt) => (
                    <div key={attempt.id} className="rounded-lg bg-background p-3">
                        <div className="flex items-center justify-between">
                            <p className="text-sm font-medium">Attempt {attempt.attempt_number}</p>
                            <StatusBadge value={attempt.status} />
                        </div>
                        <p className="text-xs text-text-secondary">{formatDate(attempt.started_at)} to {formatDate(attempt.completed_at)}</p>
                        {attempt.error_message && <p className="mt-1 text-sm text-danger">{attempt.error_message}</p>}
                    </div>
                ))}
                {attempts.length === 0 && <p className="text-sm text-text-secondary">No attempts recorded.</p>}
            </div>
        </div>
    </DetailSection>
);

const WhatsAppPanel = ({ messages }) => (
    <DetailSection title="WhatsApp & Template Preview">
        {messages.map((message) => (
            <div key={message.id} className="space-y-3 rounded-lg bg-background p-3">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Status</p>
                        <StatusBadge value={message.status} />
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Template</p>
                        <p className="text-sm text-text-primary">{message.template_name || 'No template'}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Provider</p>
                        <p className="text-sm text-text-primary">{message.provider || 'DoubleTick'}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Language</p>
                        <p className="text-sm text-text-primary">{message.language_label || message.template_language || 'N/A'}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Recipient</p>
                        <p className="text-sm text-text-primary">{message.recipient_phone_masked || 'N/A'}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Provider ID</p>
                        <p className="break-all text-sm text-text-primary">{message.provider_message_id || 'N/A'}</p>
                    </div>
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Queued</p>
                        <p className="text-sm">{formatDate(message.queued_at)}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Sent</p>
                        <p className="text-sm">{formatDate(message.sent_at)}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Delivered</p>
                        <p className="text-sm">{formatDate(message.delivered_at)}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Read</p>
                        <p className="text-sm">{formatDate(message.read_at)}</p>
                    </div>
                </div>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Created</p>
                        <p className="text-sm">{formatDate(message.created_at)}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Updated</p>
                        <p className="text-sm">{formatDate(message.updated_at)}</p>
                    </div>
                    <div>
                        <p className="text-xs font-medium uppercase text-text-secondary">Failed</p>
                        <p className="text-sm">{formatDate(message.failed_at)}</p>
                    </div>
                </div>
                {message.template_payload?.template_variables && (
                    <div className="rounded-lg border border-border bg-card p-3">
                        <p className="mb-2 text-xs font-medium uppercase text-text-secondary">Variables</p>
                        <ol className="list-decimal space-y-1 pl-5 text-sm">
                            {message.template_payload.template_variables.map((value, index) => (
                                <li key={`${message.id}-variable-${index}`} className="whitespace-pre-wrap">{value}</li>
                            ))}
                        </ol>
                    </div>
                )}
                {message.template_payload?.recommendations?.length > 0 && (
                    <div className="rounded-lg border border-border bg-card p-3">
                        <p className="mb-2 text-xs font-medium uppercase text-text-secondary">Selected Spas</p>
                        <div className="space-y-2">
                            {message.template_payload.recommendations.map((spa, index) => (
                                <div key={`${message.id}-spa-${index}`} className="text-sm">
                                    <p className="font-medium">{spa.spa_name}</p>
                                    <p className="text-text-secondary">{[spa.location, spa.open_until && `Open until ${spa.open_until}`, spa.phone].filter(Boolean).join(' • ')}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                <pre className="max-h-80 overflow-auto rounded-lg border border-border bg-card p-3 text-xs text-text-primary">
                    {JSON.stringify(message.template_payload || {}, null, 2)}
                </pre>
                {message.provider_payload && Object.keys(message.provider_payload).length > 0 && (
                    <pre className="max-h-60 overflow-auto rounded-lg border border-border bg-card p-3 text-xs text-text-primary">
                        {JSON.stringify(message.provider_payload, null, 2)}
                    </pre>
                )}
                {message.failure_reason && <p className="text-sm text-danger">Provider error: {message.failure_reason}</p>}
            </div>
        ))}
        {messages.length === 0 && <p className="text-sm text-text-secondary">No WhatsApp preparation record exists for this request.</p>}
    </DetailSection>
);

export default CallRouting;
