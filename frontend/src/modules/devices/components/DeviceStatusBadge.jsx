import React from 'react';
import Badge from '../../../shared/components/Badge';

const DeviceStatusBadge = ({ isActive, isBlocked, isRegistered, isOnline }) => {
    if (isBlocked) {
        return <Badge variant="red">Blocked</Badge>;
    }

    if (!isRegistered) {
        return <Badge variant="yellow">Pending</Badge>;
    }

    if (!isActive) {
        return <Badge variant="gray">Inactive</Badge>;
    }

    if (isOnline) {
        return <Badge variant="emerald">Online</Badge>;
    }

    return <Badge variant="rose">Offline</Badge>;
};


export default DeviceStatusBadge;
