import React from 'react';
import Badge from '../../../shared/components/Badge';
import { conversationStatusLabels, leadStatusLabels, statusVariant, formatLabel } from '../utils';

const DoubleTickStatusBadge = ({ status, type = 'conversation', size = 'md' }) => {
    const labels = type === 'lead' ? leadStatusLabels : conversationStatusLabels;
    const sizeClasses = size === 'sm' ? 'text-xs px-2 py-0.5' : size === 'lg' ? 'text-base px-3 py-1.5' : 'text-sm px-2 py-1';
    
    return (
        <Badge variant={statusVariant(status)} className={sizeClasses}>
            {labels[status] || formatLabel(status)}
        </Badge>
    );
};

export default DoubleTickStatusBadge;
