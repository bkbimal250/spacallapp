import React from 'react';
import Badge from '../../../shared/components/Badge';
import { conversationStatusLabels, leadStatusLabels, statusVariant, formatLabel } from '../utils';

const DoubleTickStatusBadge = ({ status, type = 'conversation' }) => {
    const labels = type === 'lead' ? leadStatusLabels : conversationStatusLabels;
    return (
        <Badge variant={statusVariant(status)}>
            {labels[status] || formatLabel(status)}
        </Badge>
    );
};

export default DoubleTickStatusBadge;
