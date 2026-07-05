import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import LoadingState from '../components/LoadingState';
import WebsiteLeadTable from '../components/WebsiteLeadTable';
import WebsiteWiseAnalyticsTable from '../components/WebsiteWiseAnalyticsTable';
import WebLeadStatsCards from '../components/WebLeadStatsCards';
import { getWebLeadOverviewAnalytics, getWebLeadWebsiteAnalytics, getWebsiteForms, getWebsiteLeads, updateWebsiteLead } from '../api';

const BranchWebsitePerformancePage = () => {
    const { branchId } = useParams();
    const [loading, setLoading] = useState(true);
    const [overview, setOverview] = useState({});
    const [websites, setWebsites] = useState([]);
    const [forms, setForms] = useState([]);
    const [leads, setLeads] = useState([]);

    const load = async () => {
        setLoading(true);
        try {
            const [o, w, f, l] = await Promise.all([
                getWebLeadOverviewAnalytics({ branch: branchId }),
                getWebLeadWebsiteAnalytics({ branch: branchId }),
                getWebsiteForms({ branch: branchId, is_active: true, page_size: 200 }),
                getWebsiteLeads({ branch: branchId, page_size: 10 }),
            ]);
            setOverview(o.data || {});
            setWebsites(w.data || []);
            setForms(f.data.results || f.data || []);
            setLeads(l.data.results || l.data || []);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [branchId]);

    if (loading) return <LoadingState label="Loading branch performance..." />;

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-text-primary">Branch Website Performance</h1>
            <div className="rounded-xl border border-border bg-card p-4 text-sm text-text-secondary">Active websites/forms: <span className="font-semibold text-text-primary">{forms.length}</span></div>
            <WebLeadStatsCards stats={overview} />
            <section className="rounded-xl border border-border bg-card p-4"><h2 className="mb-4 text-lg font-semibold text-text-primary">Website-wise Lead Table</h2><WebsiteWiseAnalyticsTable data={websites} /></section>
            <section className="rounded-xl border border-border bg-card p-4"><h2 className="mb-4 text-lg font-semibold text-text-primary">Recent Leads</h2><WebsiteLeadTable leads={leads} onView={(lead) => window.location.assign(`/web-leads/leads/${lead.id}`)} onStatus={async (lead, status) => { await updateWebsiteLead(lead.id, { status }); load(); }} /></section>
        </div>
    );
};

export default BranchWebsitePerformancePage;
