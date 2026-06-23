import React, { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, CircleOff, ListFilter, Send, Smartphone, Sparkles } from 'lucide-react';
import Pagination from '../../../shared/components/Pagination';
import { doubletickAPI } from '../api';
import { getCount, getList } from '../utils';
import DoubleTickTabs from '../components/DoubleTickTabs';
import LeadFilters from '../components/LeadFilters';
import LeadTable from '../components/LeadTable';
import LeadLocationCorrectionModal from '../components/LeadLocationCorrectionModal';
import LeadWindow from '../window/LeadWindow';

const pageSize = 30;
const emptyFilters = {
    status: '', location_status: '', classification: '', match_method: '',
    confidence_min: '', confidence_max: '', pending_reason: '', city: '', group: '',
    area: '', spa: '', android_visible: '', search: '', created_from: '', created_to: '',
};

const queueTabs = [
    { key: 'all', label: 'All Leads', icon: ListFilter, params: {} },
    { key: 'pending', label: 'Pending / Unmatched', icon: CircleOff, params: { location_status: 'pending' } },
    { key: 'matched', label: 'Matched', icon: CheckCircle2, params: { location_status: 'matched' } },
    { key: 'sent', label: 'Sent to Android', icon: Smartphone, params: { android_visible: 'true' } },
    { key: 'job', label: 'Job Inquiry', icon: Sparkles, params: { classification: 'job_inquiry' } },
    { key: 'closed', label: 'Closed / Lost', icon: Send, params: { queue: 'closed_lost' } },
];

const DoubleTickLeads = () => {
    const [filters, setFilters] = useState(emptyFilters);
    const [activeQueue, setActiveQueue] = useState('all');
    const [leads, setLeads] = useState([]);
    const [totalCount, setTotalCount] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState(null);
    const [correctingLead, setCorrectingLead] = useState(null);

    const fetchLeads = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, page_size: pageSize, ...(queueTabs.find((item) => item.key === activeQueue)?.params || {}) };
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== '') params[key] = value;
            });
            const response = await doubletickAPI.getLeads(params);
            setLeads(getList(response));
            setTotalCount(getCount(response));
        } catch (error) {
            console.error('Failed to fetch DoubleTick leads', error);
        } finally {
            setLoading(false);
        }
    }, [activeQueue, filters, page]);

    useEffect(() => { fetchLeads(); }, [fetchLeads]);

    const selectQueue = (key) => {
        setActiveQueue(key);
        setPage(1);
    };

    return (
        <div className="space-y-5">
            <div className="space-y-2">
                <h1 className="text-2xl font-bold text-text-primary">DoubleTick Location Leads</h1>
                <p className="text-sm text-text-secondary">Review pending location matches, apply safe suggestions, and control when leads become visible in SuperCall.</p>
            </div>
            <DoubleTickTabs />

            <div className="flex gap-1 overflow-x-auto rounded-lg border border-border bg-card p-1">
                {queueTabs.map((tab) => (
                    <button key={tab.key} type="button" onClick={() => selectQueue(tab.key)}
                        className={`inline-flex shrink-0 items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${activeQueue === tab.key ? 'bg-primary text-white shadow-sm' : 'text-text-secondary hover:bg-background hover:text-text-primary'}`}>
                        <tab.icon size={15} /> {tab.label}
                    </button>
                ))}
            </div>

            <LeadFilters filters={filters} onChange={(next) => { setFilters(next); setPage(1); }}
                onReset={() => { setFilters(emptyFilters); setPage(1); }} onRefresh={fetchLeads} />

            <div className="overflow-hidden rounded-lg border border-border bg-card">
                {loading ? (
                    <div className="p-12 text-center text-text-secondary">Loading location leads...</div>
                ) : (
                    <LeadTable leads={leads} onOpen={(row) => setSelectedId(row.id)}
                        onCorrect={setCorrectingLead} onChanged={fetchLeads} />
                )}
                <Pagination currentPage={page} totalPages={Math.ceil(totalCount / pageSize)}
                    onPageChange={setPage} totalCount={totalCount} pageSize={pageSize} />
            </div>

            <LeadWindow isOpen={Boolean(selectedId)} leadId={selectedId}
                onClose={() => setSelectedId(null)} onChanged={fetchLeads} />
            <LeadLocationCorrectionModal isOpen={Boolean(correctingLead)} lead={correctingLead}
                onClose={() => setCorrectingLead(null)} onSaved={fetchLeads} />
        </div>
    );
};

export default DoubleTickLeads;
