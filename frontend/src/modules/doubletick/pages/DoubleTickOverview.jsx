import React, { useEffect, useState } from 'react';
import { AlertCircle, Inbox, RefreshCw, Send } from 'lucide-react';
import Button from '../../../shared/components/Button';
import DoubleTickMetricGrid from '../components/DoubleTickMetricGrid';
import DoubleTickTabs from '../components/DoubleTickTabs';
import { doubletickAPI } from '../api';

const DoubleTickOverview = () => {
    const [metrics, setMetrics] = useState({});
    const [loading, setLoading] = useState(true);

    const fetchMetrics = async () => {
        setLoading(true);
        try {
            const response = await doubletickAPI.getMetrics();
            setMetrics(response.data || {});
        } catch (error) {
            console.error('Failed to fetch DoubleTick metrics', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMetrics();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">DoubleTick WhatsApp</h1>
                    <p className="text-sm text-text-secondary">Pending conversations, area qualification, distribution and claim tracking.</p>
                </div>
                <Button variant="secondary" className="gap-2" onClick={fetchMetrics} loading={loading}>
                    <RefreshCw size={16} />
                    Refresh
                </Button>
            </div>

            <DoubleTickTabs />
            <DoubleTickMetricGrid metrics={metrics} loading={loading} />

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                <div className="bg-card border border-border rounded-lg p-5 space-y-2">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="bg-warning/10 text-warning rounded-lg p-2">
                            <Inbox className="text-warning" size={20} />
                        </div>
                        <h2 className="font-semibold text-text-primary">1. Pending Queue</h2>
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">
                        Conversations that need manual CRM confirmation: greetings only, missing location data, or services we don't support. CRM team reviews and matches these to official areas.
                    </p>
                    <div className="pt-2">
                        <a href="/doubletick/conversations" className="text-primary text-sm font-medium hover:underline">View pending →</a>
                    </div>
                </div>

                <div className="bg-card border border-border rounded-lg p-5 space-y-2">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="bg-primary/10 text-primary rounded-lg p-2">
                            <Send className="text-primary" size={20} />
                        </div>
                        <h2 className="font-semibold text-text-primary">2. Area Distribution</h2>
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">
                        Once an area is confirmed and branches are mapped, it becomes an available lead. Mapped branches receive notifications and can claim leads in their areas.
                    </p>
                    <div className="pt-2">
                        <a href="/doubletick/leads" className="text-primary text-sm font-medium hover:underline">View leads →</a>
                    </div>
                </div>

                <div className="bg-card border border-border rounded-lg p-5 space-y-2">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="bg-danger/10 text-danger rounded-lg p-2">
                            <AlertCircle className="text-danger" size={20} />
                        </div>
                        <h2 className="font-semibold text-text-primary">3. One Active Owner</h2>
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">
                        The first manager who claims a lead becomes the owner. Only they can start contact, mark it as contacted, or move to follow-up. Others can't interact until the lead is released.
                    </p>
                    <div className="pt-2">
                        <a href="/doubletick/area-map" className="text-primary text-sm font-medium hover:underline">View mappings →</a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DoubleTickOverview;
