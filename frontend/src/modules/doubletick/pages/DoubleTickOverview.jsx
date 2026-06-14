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
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="flex items-center gap-3 mb-3">
                        <Inbox className="text-warning" size={22} />
                        <h2 className="font-semibold">Pending Queue</h2>
                    </div>
                    <p className="text-sm text-text-secondary">Greeting-only, missing-location and incomplete bot conversations stay here until the CRM team confirms area/service.</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="flex items-center gap-3 mb-3">
                        <Send className="text-primary" size={22} />
                        <h2 className="font-semibold">Area Distribution</h2>
                    </div>
                    <p className="text-sm text-text-secondary">Only confirmed CRM areas become available leads. Mapped branches receive visibility and notifications.</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-5">
                    <div className="flex items-center gap-3 mb-3">
                        <AlertCircle className="text-danger" size={22} />
                        <h2 className="font-semibold">One Active Owner</h2>
                    </div>
                    <p className="text-sm text-text-secondary">The first manager claim wins. Contact actions are restricted to the active owner until release or reassignment.</p>
                </div>
            </div>
        </div>
    );
};

export default DoubleTickOverview;
