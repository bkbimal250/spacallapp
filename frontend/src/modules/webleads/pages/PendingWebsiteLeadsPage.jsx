import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Pagination from '../../../shared/components/Pagination';
import LoadingState from '../components/LoadingState';
import PendingLeadAssignModal from '../components/PendingLeadAssignModal';
import WebsiteLeadFilters from '../components/WebsiteLeadFilters';
import WebsiteLeadTable from '../components/WebsiteLeadTable';
import { assignWebsiteLead, getWebsiteLeads, updateWebsiteLead } from '../api';

const pageSize = 50;

const PendingWebsiteLeadsPage = () => {
    const navigate = useNavigate();
    const [leads, setLeads] = useState([]);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [assigning, setAssigning] = useState(null);

    const load = async () => {
        setLoading(true);
        setError('');
        try {
            const [pending, unassigned] = await Promise.all([
                getWebsiteLeads({ ...filters, routing_status: 'pending_configuration', page, page_size: pageSize }),
                getWebsiteLeads({ ...filters, routing_status: 'unassigned', page, page_size: pageSize }),
            ]);
            const rows = [...(pending.data.results || pending.data || []), ...(unassigned.data.results || unassigned.data || [])];
            setLeads(rows);
            setTotal((pending.data.count || rows.length) + (unassigned.data.count || 0));
        } catch (err) {
            console.error('Failed to load pending website leads', err);
            setLeads([]);
            setTotal(0);
            setError(err?.response?.data?.detail || 'Unable to load pending website leads. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [filters, page]);

    const status = async (lead, nextStatus) => {
        setError('');
        try {
            await updateWebsiteLead(lead.id, { status: nextStatus });
            load();
        } catch (err) {
            console.error('Failed to update pending website lead', err);
            setError(err?.response?.data?.detail || 'Unable to update this lead.');
        }
    };

    const assign = async (payload) => {
        if (!assigning?.id) return;
        setError('');
        try {
            await assignWebsiteLead(assigning.id, payload);
            setAssigning(null);
            load();
        } catch (err) {
            console.error('Failed to assign pending website lead', err);
            setError(err?.response?.data?.detail || 'Unable to assign this lead.');
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-text-primary">Pending Website Leads</h1>
            <div className="rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">Only pending configuration and unassigned website leads are shown here.</div>
            <div className="rounded-xl border border-border bg-card p-4"><WebsiteLeadFilters pendingOnly onFilter={(next) => { setFilters(next); setPage(1); }} /></div>
            {error && (
                <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
                    {error}
                </div>
            )}
            <div className="rounded-xl border border-border bg-card">
                {loading ? <LoadingState /> : <WebsiteLeadTable leads={leads} onView={(row) => navigate(`/web-leads/leads/${row.id}`)} onStatus={status} onAssign={setAssigning} canAssign pendingOnly />}
                {!loading && total > 0 && <Pagination currentPage={page} totalPages={Math.ceil(total / pageSize)} onPageChange={setPage} totalCount={total} pageSize={pageSize} />}
            </div>
            <PendingLeadAssignModal lead={assigning} isOpen={Boolean(assigning)} onClose={() => setAssigning(null)} onSubmit={assign} />
        </div>
    );
};

export default PendingWebsiteLeadsPage;
