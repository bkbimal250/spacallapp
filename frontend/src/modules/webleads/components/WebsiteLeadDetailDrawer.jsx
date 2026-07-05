import React from 'react';
import Modal from '../../../shared/components/Modal';
import { formatDate } from '../../../shared/utils/formatDate';
import CopyButton from './CopyButton';
import LeadStatusBadge from './LeadStatusBadge';
import RoutingStatusBadge from './RoutingStatusBadge';
import NotificationStatusBadge from './NotificationStatusBadge';

const Row = ({ label, value }) => (
    <div>
        <p className="text-xs font-semibold uppercase text-text-muted">{label}</p>
        <p className="mt-1 text-sm text-text-primary">{value || '-'}</p>
    </div>
);

const DetailContent = ({ lead }) => (
    <div className="space-y-6">
            <section className="grid gap-4 md:grid-cols-2">
                <Row label="Customer Name" value={lead?.customer_name} />
                <div><Row label="Phone" value={lead?.phone} />{lead?.phone && <CopyButton value={lead.phone} label="Copy phone" className="mt-2" />}</div>
                <Row label="Address" value={lead?.address} />
                <Row label="Notes" value={lead?.notes} />
            </section>
            <section className="grid gap-4 md:grid-cols-2">
                <Row label="Website Name" value={lead?.website_name} />
                <Row label="Website URL" value={lead?.website_url} />
                <Row label="Form Key" value={lead?.form_key} />
                <Row label="Submitted From URL" value={lead?.submitted_from_url} />
                <Row label="Referrer URL" value={lead?.referrer_url} />
            </section>
            <section className="grid gap-4 md:grid-cols-2">
                <Row label="Branch/Spa" value={lead?.branch_name} />
                <div><p className="text-xs font-semibold uppercase text-text-muted">Routing Status</p><div className="mt-1"><RoutingStatusBadge status={lead?.routing_status} /></div></div>
                <Row label="Assigned To" value={lead?.assigned_to_name} />
                <div><p className="text-xs font-semibold uppercase text-text-muted">Status</p><div className="mt-1"><LeadStatusBadge status={lead?.status} /></div></div>
                <div><p className="text-xs font-semibold uppercase text-text-muted">Notification Status</p><div className="mt-1"><NotificationStatusBadge status={lead?.notification_status} /></div></div>
                <Row label="Notification Error" value={lead?.notification_error} />
            </section>
            <section className="rounded-xl border border-border bg-background p-4">
                <h3 className="mb-3 text-sm font-semibold text-text-primary">Timeline</h3>
                <div className="space-y-2 text-sm text-text-secondary">
                    <p>Submitted: {formatDate(lead?.created_at, 'MMM dd, yyyy HH:mm') || '-'}</p>
                    <p>Routed: {lead?.routing_status === 'routed' ? 'Yes' : 'No'}</p>
                    <p>Notification: {lead?.notification_status || '-'}</p>
                    <p>Status changed: {formatDate(lead?.updated_at, 'MMM dd, yyyy HH:mm') || '-'}</p>
                    <p>Manually assigned: {lead?.assigned_to_name ? 'Yes' : 'No'}</p>
                </div>
            </section>
    </div>
);

const WebsiteLeadDetailDrawer = ({ lead, isOpen, onClose, embedded = false }) => {
    if (embedded) {
        return (
            <div className="rounded-xl border border-border bg-card p-5">
                <DetailContent lead={lead} />
            </div>
        );
    }

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Website Lead Detail" maxWidth="max-w-3xl">
            <DetailContent lead={lead} />
        </Modal>
    );
};

export default WebsiteLeadDetailDrawer;
