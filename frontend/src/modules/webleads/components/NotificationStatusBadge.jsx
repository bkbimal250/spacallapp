import React from 'react';

const styles = {
    pending: 'bg-warning/10 text-warning border-warning/20',
    sent: 'bg-success/10 text-success border-success/20',
    failed: 'bg-danger/10 text-danger border-danger/20',
    not_required: 'bg-background text-text-secondary border-border',
};

const labels = {
    pending: 'Pending',
    sent: 'Sent',
    failed: 'Failed',
    not_required: 'Not required',
};

const NotificationStatusBadge = ({ status }) => (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${styles[status] || 'bg-background text-text-secondary border-border'}`}>
        {labels[status] || status || 'Unknown'}
    </span>
);

export default NotificationStatusBadge;
