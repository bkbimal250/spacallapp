import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../../../shared/components/Button';
import Pagination from '../../../shared/components/Pagination';
import LoadingState from '../components/LoadingState';
import WebsiteFormFilters from '../components/WebsiteFormFilters';
import WebsiteFormTable from '../components/WebsiteFormTable';
import { deleteWebsiteForm, getWebsiteForms, updateWebsiteForm } from '../api';

const pageSize = 50;

const WebsiteFormsPage = () => {
    const navigate = useNavigate();
    const [forms, setForms] = useState([]);
    const [filters, setFilters] = useState({});
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        try {
            const res = await getWebsiteForms({ ...filters, page, page_size: pageSize });
            const rows = res.data.results || res.data || [];
            setForms(rows);
            setTotal(res.data.count || rows.length);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [filters, page]);

    const remove = async (row) => {
        if (!window.confirm('Delete this website form?')) return;
        await deleteWebsiteForm(row.id);
        load();
    };

    const toggle = async (row) => {
        await updateWebsiteForm(row.id, { is_active: !row.is_active });
        load();
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between gap-3">
                <h1 className="text-2xl font-semibold text-text-primary">Website Forms</h1>
                <Link to="/web-leads/forms/create"><Button>Create Website Form</Button></Link>
            </div>
            <div className="rounded-xl border border-border bg-card p-4"><WebsiteFormFilters onFilter={(next) => { setFilters(next); setPage(1); }} /></div>
            <div className="rounded-xl border border-border bg-card">
                {loading ? <LoadingState label="Loading website forms..." /> : <WebsiteFormTable forms={forms} onView={(row) => navigate(`/web-leads/forms/${row.id}`)} onEdit={(row) => navigate(`/web-leads/forms/${row.id}/edit`)} onToggle={toggle} onDelete={remove} onLeads={(row) => navigate(`/web-leads/leads?form_key=${row.form_key}`)} onAnalytics={(row) => navigate(`/web-leads/analytics?form_key=${row.form_key}`)} />}
                {!loading && total > 0 && <Pagination currentPage={page} totalPages={Math.ceil(total / pageSize)} onPageChange={setPage} totalCount={total} pageSize={pageSize} />}
            </div>
        </div>
    );
};

export default WebsiteFormsPage;
