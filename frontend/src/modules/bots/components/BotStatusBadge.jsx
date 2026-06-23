import React from 'react';
import Badge from '../../../shared/components/Badge';
import { formatLabel, statusVariant } from '../utils';

const BotStatusBadge = ({ status, active }) => {
    const value = typeof active === 'boolean' ? (active ? 'active' : 'inactive') : status;
    return <Badge variant={statusVariant(value)}>{formatLabel(value)}</Badge>;
};

export default BotStatusBadge;
