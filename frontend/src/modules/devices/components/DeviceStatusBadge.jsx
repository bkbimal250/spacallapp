import React from 'react';
import Badge from '../../../shared/components/Badge';

const DeviceStatusBadge = ({ isActive, isBlocked, isRegistered }) => {
    if (isBlocked) {
        return <Badge variant="red">Blocked</Badge>;
    }

    if (!isRegistered) {
        return <Badge variant="yellow">Pending</Badge>;
    }

    if (isActive) {
        return <Badge variant="green">Active</Badge>;
    }

    return <Badge variant="gray">Inactive</Badge>;
};


export default DeviceStatusBadge;
