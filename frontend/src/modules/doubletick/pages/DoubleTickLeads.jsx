import React, { useCallback, useEffect, useState } from 'react';
import Pagination from '../../../shared/components/Pagination';
import { doubletickAPI } from '../api';
import { getCount, getList } from '../utils';
import DoubleTickTabs from '../components/DoubleTickTabs';
import LeadFilters from '../components/LeadFilters';
import LeadTable from '../components/LeadTable';
import LeadWindow from '../window/LeadWindow';

const pageSize = 30;

const DoubleTickLeads = () => {
    const [filters, setFilters] = useState({ status: '', available: '', matched_area: '', search: '' });
    const [leads, setLeads] = useState([]);
    const [totalCount, setTotalCount] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState(null);

    const fetchLeads = useCallback(async () => {
        setLoading(true);
        try {
            const params = { page, page_size: pageSize };
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
    }, [filters, page]);

    useEffect(() => {
        fetchLeads();
    }, [fetchLeads]);

    const reset = () => {
        setFilters({ status: '', available: '', matched_area: '', search: '' });
        setPage(1);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-text-primary">DoubleTick Area Leads</h1>
                <p className="text-sm text-text-secondary">Qualified WhatsApp leads distributed to mapped branches with claim and contact history.</p>
            </div>
            <DoubleTickTabs />
            <LeadFilters filters={filters} onChange={(next) => { setFilters(next); setPage(1); }} onReset={reset} onRefresh={fetchLeads} />
            <div className="bg-card border border-border rounded-lg overflow-hidden">
                {loading ? (
                    <div className="p-12 text-center text-text-secondary">Loading leads...</div>
                ) : (
                    <LeadTable leads={leads} onOpen={(row) => setSelectedId(row.id)} />
                )}
                <Pagination currentPage={page} totalPages={Math.ceil(totalCount / pageSize)} onPageChange={setPage} totalCount={totalCount} pageSize={pageSize} />
            </div>
            <LeadWindow
                isOpen={Boolean(selectedId)}
                leadId={selectedId}
                onClose={() => setSelectedId(null)}
                onChanged={fetchLeads}
            />
        </div>
    );
};

export default DoubleTickLeads;
