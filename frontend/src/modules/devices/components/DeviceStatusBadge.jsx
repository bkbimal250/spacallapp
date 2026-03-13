import React from 'react';
import Badge from '../../../shared/components/Badge';

const DeviceStatusBadge = ({ isActive, isBlocked, isRegistered, isOnline }) => {

    if (isBlocked) {
        return <Badge variant="danger">Blocked</Badge>;
    }

    if (!isRegistered) {
        return <Badge variant="warning">Pending</Badge>;
    }

    if (!isActive) {
        return <Badge variant="secondary">Inactive</Badge>;
    }

    if (isOnline) {
        return <Badge variant="success">Online</Badge>;
    }

    return <Badge variant="danger">Offline</Badge>;
};

export default DeviceStatusBadge;