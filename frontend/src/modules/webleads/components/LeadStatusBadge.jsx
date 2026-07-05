import React from 'react';

const styles = {
    new: 'bg-info/10 text-info border-info/20',
    contacted: 'bg-primary/10 text-primary border-primary/20',
    converted: 'bg-success/10 text-success border-success/20',
    rejected: 'bg-danger/10 text-danger border-danger/20',
    duplicate: 'bg-warning/10 text-warning border-warning/20',
};

const labels = {
    new: 'New',
    contacted: 'Contacted',
    converted: 'Converted',
    rejected: 'Rejected',
    duplicate: 'Duplicate',
};

const LeadStatusBadge = ({ status }) => (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold ${styles[status] || 'bg-background text-text-secondary border-border'}`}>
        {labels[status] || status || 'Unknown'}
    </span>
);

export default LeadStatusBadge;
