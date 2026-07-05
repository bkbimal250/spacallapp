import React from 'react';

const styles = {
    routed: 'bg-success/10 text-success border-success/20',
    pending_configuration: 'bg-warning/10 text-warning border-warning/20',
    unassigned: 'bg-danger/10 text-danger border-danger/20',
};

const labels = {
    routed: 'Routed',
    pending_configuration: 'Pending configuration',
    unassigned: 'Unassigned',
};

const RoutingStatusBadge = ({ status }) => (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${styles[status] || 'bg-background text-text-secondary border-border'}`}>
        {labels[status] || status || 'Unknown'}
    </span>
);

export default RoutingStatusBadge;
