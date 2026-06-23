import React from 'react';
import { Building2, CheckCircle2, Smartphone, UserRound, XCircle } from 'lucide-react';
import Button from '../../../shared/components/Button';

const Metric = ({ icon: Icon, label, value }) => (
    <div className="rounded-lg border border-border bg-card/60 p-3">
        <Icon size={15} className="mb-2 text-primary" />
        <p className="text-xs text-text-secondary">{label}</p>
        <p className="font-semibold text-text-primary">{value}</p>
    </div>
);

const AndroidVisibilityPanel = ({ lead, onSend, loading = false }) => {
    const visible = lead?.visibilities?.filter((item) => item.is_visible) || [];
    const devices = visible.filter((item) => item.device);
    const users = visible.filter((item) => item.user);
    const branches = [...new Set(visible.map((item) => item.branch_name).filter(Boolean))];
    const audit = lead?.latest_distribution_audit;
    const sent = devices.length > 0 || lead?.sent_to_android;
    const canSend = Boolean(lead?.matched_area);

    return (
        <div className="rounded-lg border border-border bg-background p-4 space-y-3">
            <div className="flex items-center justify-between gap-3">
                <div>
                    <p className="font-semibold text-text-primary">Android Visibility</p>
                    <p className="text-xs text-text-secondary">SuperCall distribution and ownership</p>
                </div>
                <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${sent ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                    {sent ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                    {sent ? 'Visible' : 'Not sent'}
                </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
                <Metric icon={Building2} label="Branches" value={branches.length} />
                <Metric icon={UserRound} label="Users" value={users.length || lead?.android_user_count || 0} />
                <Metric icon={Smartphone} label="Devices" value={devices.length || lead?.android_device_count || 0} />
            </div>
            <div className="text-xs text-text-secondary space-y-1">
                <p>Owner: <span className="text-text-primary">{lead?.current_user_name || lead?.assigned_user_name || 'Unclaimed'}</span></p>
                <p>Claim: <span className="text-text-primary">{lead?.active_assignment_detail?.status || lead?.status || '-'}</span></p>
                <p>Distribution: <span className="text-text-primary">{audit?.status || 'Not attempted'}</span></p>
                {audit?.failure_reason && <p className="text-danger">{audit.failure_reason}</p>}
            </div>
            <Button className="w-full justify-center" loading={loading} disabled={!canSend} onClick={onSend}>
                <Smartphone size={16} />
                {sent ? 'Re-distribute to Android' : 'Send to Android'}
            </Button>
            {!canSend && <p className="text-xs text-warning">Confirm an area or branch before sending.</p>}
        </div>
    );
};

export default AndroidVisibilityPanel;
