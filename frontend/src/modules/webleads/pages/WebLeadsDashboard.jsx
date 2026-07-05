import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import LoadingState from '../components/LoadingState';
import WebLeadStatsCards from '../components/WebLeadStatsCards';
import WebsiteLeadTable from '../components/WebsiteLeadTable';
import WebsiteWiseAnalyticsTable from '../components/WebsiteWiseAnalyticsTable';
import { getWebLeadOverviewAnalytics, getWebLeadWebsiteAnalytics, getWebsiteLeads, updateWebsiteLead } from '../api';

const WebLeadsDashboard = () => {
    const [stats, setStats] = useState({});
    const [leads, setLeads] = useState([]);
    const [websites, setWebsites] = useState([]);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        try {
            const [overview, recent, websiteRows] = await Promise.all([
                getWebLeadOverviewAnalytics(),
                getWebsiteLeads({ page_size: 10 }),
                getWebLeadWebsiteAnalytics(),
            ]);
            setStats(overview.data || {});
            setLeads(recent.data.results || recent.data || []);
            setWebsites((websiteRows.data || []).slice(0, 8));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    const updateStatus = async (lead, status) => {
        await updateWebsiteLead(lead.id, { status });
        load();
    };

    if (loading) return <LoadingState />;

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <h1 className="text-2xl font-semibold text-text-primary">Website Leads Dashboard</h1>
                <div className="flex flex-wrap gap-2">
                    <Link className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-hover" to="/web-leads/forms/create">Create Website Form</Link>
                    <Link className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-background" to="/web-leads/leads">View Website Leads</Link>
                    <Link className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-background" to="/web-leads/pending">View Pending Leads</Link>
                    <Link className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-background" to="/web-leads/analytics">View Analytics</Link>
                </div>
            </div>
            <WebLeadStatsCards stats={stats} />
            {(stats.pending_unassigned_leads > 0 || stats.notification_failed_count > 0) && (
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">Pending leads need branch assignment.</div>
                    <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">Notification failures need review.</div>
                </div>
            )}
            <section className="rounded-xl border border-border bg-card p-4">
                <h2 className="mb-4 text-lg font-semibold text-text-primary">Recent Website Leads</h2>
                <WebsiteLeadTable leads={leads} onView={(row) => window.location.assign(`/web-leads/leads/${row.id}`)} onStatus={updateStatus} />
            </section>
            <section className="rounded-xl border border-border bg-card p-4">
                <h2 className="mb-4 text-lg font-semibold text-text-primary">Top Performing Websites</h2>
                <WebsiteWiseAnalyticsTable data={websites} />
            </section>
        </div>
    );
};

export default WebLeadsDashboard;
