import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Button from '../../../shared/components/Button';
import { useAuth } from '../../../shared/hooks/useAuth';
import LoadingState from '../components/LoadingState';
import PendingLeadAssignModal from '../components/PendingLeadAssignModal';
import WebsiteLeadDetailDrawer from '../components/WebsiteLeadDetailDrawer';
import { assignWebsiteLead, getWebsiteLead, updateWebsiteLead } from '../api';

const WebsiteLeadDetailPage = () => {
    const { id } = useParams();
    const { user } = useAuth();
    const canAssign = ['admin', 'super_admin'].includes(user?.role);
    const [lead, setLead] = useState(null);
    const [assignOpen, setAssignOpen] = useState(false);
    const [savingAssign, setSavingAssign] = useState(false);

    const load = async () => {
        const res = await getWebsiteLead(id);
        setLead(res.data);
    };

    useEffect(() => {
        load();
    }, [id]);

    const status = async (nextStatus) => {
        await updateWebsiteLead(id, { status: nextStatus });
        load();
    };

    const assign = async (payload) => {
        setSavingAssign(true);
        try {
            await assignWebsiteLead(id, payload);
            setAssignOpen(false);
            load();
        } finally {
            setSavingAssign(false);
        }
    };

    if (!lead) return <LoadingState label="Loading website lead..." />;

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-semibold text-text-primary">{lead.customer_name}</h1>
                    <Link className="text-sm text-primary" to="/web-leads/leads">Back to leads</Link>
                </div>
                <div className="flex flex-wrap gap-2">
                    {['contacted', 'converted', 'rejected'].map((item) => <Button key={item} variant="secondary" onClick={() => status(item)}>{item}</Button>)}
                    {canAssign && <Button onClick={() => setAssignOpen(true)}>Assign Branch</Button>}
                </div>
            </div>
            <WebsiteLeadDetailDrawer lead={lead} embedded />
            <PendingLeadAssignModal lead={lead} isOpen={assignOpen} onClose={() => setAssignOpen(false)} onSubmit={assign} saving={savingAssign} />
        </div>
    );
};

export default WebsiteLeadDetailPage;
