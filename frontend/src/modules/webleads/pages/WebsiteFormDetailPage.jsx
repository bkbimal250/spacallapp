import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Button from '../../../shared/components/Button';
import { formatDate } from '../../../shared/utils/formatDate';
import LoadingState from '../components/LoadingState';
import WebsiteFormIntegrationCode from '../components/WebsiteFormIntegrationCode';
import WebsiteFormPreview from '../components/WebsiteFormPreview';
import WebsiteLeadTable from '../components/WebsiteLeadTable';
import WebLeadStatsCards from '../components/WebLeadStatsCards';
import CopyButton from '../components/CopyButton';
import { getWebLeadOverviewAnalytics, getWebsiteForm, getWebsiteLeads, updateWebsiteLead } from '../api';

const WebsiteFormDetailPage = () => {
    const { id } = useParams();
    const [form, setForm] = useState(null);
    const [stats, setStats] = useState({});
    const [leads, setLeads] = useState([]);

    const load = async () => {
        const formRes = await getWebsiteForm(id);
        setForm(formRes.data);
        const [overview, leadRows] = await Promise.all([
            getWebLeadOverviewAnalytics({ form_key: formRes.data.form_key }),
            getWebsiteLeads({ form_key: formRes.data.form_key, page_size: 10 }),
        ]);
        setStats(overview.data || {});
        setLeads(leadRows.data.results || leadRows.data || []);
    };

    useEffect(() => {
        load();
    }, [id]);

    if (!form) return <LoadingState label="Loading website form..." />;

    const row = (label, value) => <div><p className="text-xs font-semibold uppercase text-text-muted">{label}</p><p className="mt-1 text-sm text-text-primary">{value || '-'}</p></div>;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between gap-3">
                <h1 className="text-2xl font-semibold text-text-primary">{form.website_name}</h1>
                <Link to={`/web-leads/forms/${id}/edit`}><Button>Edit</Button></Link>
            </div>
            <section className="grid gap-4 rounded-xl border border-border bg-card p-5 md:grid-cols-3">
                {row('Website URL', form.website_url)}
                {row('Branch/Spa', form.branch_name)}
                <div>{row('Form Key', form.form_key)}<CopyButton value={form.form_key} label="Copy key" className="mt-2" /></div>
                {row('Status', form.is_active ? 'Active' : 'Inactive')}
                {row('Created At', formatDate(form.created_at, 'MMM dd, yyyy HH:mm'))}
                {row('Updated At', formatDate(form.updated_at, 'MMM dd, yyyy HH:mm'))}
            </section>
            <WebsiteFormIntegrationCode form={form} />
            <WebsiteFormPreview form={form} />
            <WebLeadStatsCards stats={stats} />
            <section className="rounded-xl border border-border bg-card p-4">
                <h2 className="mb-4 text-lg font-semibold text-text-primary">Recent Leads</h2>
                <WebsiteLeadTable leads={leads} onView={(lead) => window.location.assign(`/web-leads/leads/${lead.id}`)} onStatus={async (lead, status) => { await updateWebsiteLead(lead.id, { status }); load(); }} />
            </section>
        </div>
    );
};

export default WebsiteFormDetailPage;
