import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Pagination from '../../../shared/components/Pagination';
import { useAuth } from '../../../shared/hooks/useAuth';
import LoadingState from '../components/LoadingState';
import PendingLeadAssignModal from '../components/PendingLeadAssignModal';
import WebsiteLeadFilters from '../components/WebsiteLeadFilters';
import WebsiteLeadTable from '../components/WebsiteLeadTable';
import { assignWebsiteLead, deleteWebsiteLead, getWebsiteLeads, updateWebsiteLead } from '../api';

const pageSize = 50;

const WebsiteLeadsPage = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { user } = useAuth();
    const canAssign = ['admin', 'super_admin'].includes(user?.role);
    const canDelete = user?.role === 'super_admin';
    const [leads, setLeads] = useState([]);
    const [filters, setFilters] = useState({ form_key: searchParams.get('form_key') || '' });
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [assigning, setAssigning] = useState(null);
    const [savingAssign, setSavingAssign] = useState(false);

    const load = async () => {
        setLoading(true);
        try {
            const res = await getWebsiteLeads({ ...filters, page, page_size: pageSize });
            const rows = res.data.results || res.data || [];
            setLeads(rows);
            setTotal(res.data.count || rows.length);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [filters, page]);

    const status = async (lead, nextStatus) => {
        await updateWebsiteLead(lead.id, { status: nextStatus });
        load();
    };

    const assign = async (payload) => {
        setSavingAssign(true);
        try {
            await assignWebsiteLead(assigning.id, payload);
            setAssigning(null);
            load();
        } finally {
            setSavingAssign(false);
        }
    };

    const remove = async (lead) => {
        if (!window.confirm('Delete this website lead?')) return;
        await deleteWebsiteLead(lead.id);
        load();
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-text-primary">Website Leads</h1>
            <div className="rounded-xl border border-border bg-card p-4"><WebsiteLeadFilters initialFilters={filters} onFilter={(next) => { setFilters(next); setPage(1); }} /></div>
            <div className="rounded-xl border border-border bg-card">
                {loading ? <LoadingState /> : <WebsiteLeadTable leads={leads} onView={(row) => navigate(`/web-leads/leads/${row.id}`)} onStatus={status} onAssign={setAssigning} onDelete={remove} canAssign={canAssign} canDelete={canDelete} />}
                {!loading && total > 0 && <Pagination currentPage={page} totalPages={Math.ceil(total / pageSize)} onPageChange={setPage} totalCount={total} pageSize={pageSize} />}
            </div>
            <PendingLeadAssignModal lead={assigning} isOpen={Boolean(assigning)} onClose={() => setAssigning(null)} onSubmit={assign} saving={savingAssign} />
        </div>
    );
};

export default WebsiteLeadsPage;
