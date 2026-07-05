import React, { useEffect, useState } from 'react';
import LoadingState from '../components/LoadingState';
import WebLeadStatsCards from '../components/WebLeadStatsCards';
import BranchWiseAnalyticsTable from '../components/BranchWiseAnalyticsTable';
import WebsiteWiseAnalyticsTable from '../components/WebsiteWiseAnalyticsTable';
import FormKeyAnalyticsTable from '../components/FormKeyAnalyticsTable';
import WebsiteLeadFilters from '../components/WebsiteLeadFilters';
import { getWebLeadBranchAnalytics, getWebLeadFormAnalytics, getWebLeadOverviewAnalytics, getWebLeadWebsiteAnalytics } from '../api';

const WebLeadAnalyticsPage = () => {
    const [filters, setFilters] = useState({});
    const [loading, setLoading] = useState(true);
    const [overview, setOverview] = useState({});
    const [branches, setBranches] = useState([]);
    const [websites, setWebsites] = useState([]);
    const [forms, setForms] = useState([]);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const [o, b, w, f] = await Promise.all([
                    getWebLeadOverviewAnalytics(filters),
                    getWebLeadBranchAnalytics(filters),
                    getWebLeadWebsiteAnalytics(filters),
                    getWebLeadFormAnalytics(filters),
                ]);
                setOverview(o.data || {});
                setBranches(b.data || []);
                setWebsites(w.data || []);
                setForms(f.data || []);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [filters]);

    if (loading) return <LoadingState label="Loading analytics..." />;

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-semibold text-text-primary">Website Lead Analytics</h1>
            <div className="rounded-xl border border-border bg-card p-4"><WebsiteLeadFilters onFilter={setFilters} /></div>
            <WebLeadStatsCards stats={overview} />
            <section className="rounded-xl border border-border bg-card p-4"><h2 className="mb-4 text-lg font-semibold text-text-primary">Branch-wise Leads</h2><BranchWiseAnalyticsTable data={branches} /></section>
            <section className="rounded-xl border border-border bg-card p-4"><h2 className="mb-4 text-lg font-semibold text-text-primary">Website-wise Leads</h2><WebsiteWiseAnalyticsTable data={websites} /></section>
            <section className="rounded-xl border border-border bg-card p-4"><h2 className="mb-4 text-lg font-semibold text-text-primary">Form-key-wise Analytics</h2><FormKeyAnalyticsTable data={forms} /></section>
            <section className="rounded-xl border border-border bg-card p-4">
                <h2 className="mb-4 text-lg font-semibold text-text-primary">Lead Status Breakdown</h2>
                <div className="grid gap-3 sm:grid-cols-5">
                    {['new', 'contacted', 'converted', 'rejected', 'duplicate'].map((status) => <div key={status} className="rounded-lg border border-border bg-background p-3 text-sm font-semibold capitalize text-text-primary">{status}</div>)}
                </div>
            </section>
        </div>
    );
};

export default WebLeadAnalyticsPage;
