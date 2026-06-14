export const conversationStatusLabels = {
    new: 'New',
    pending: 'Pending',
    awaiting_customer: 'Awaiting Customer',
    awaiting_location: 'Awaiting Location',
    awaiting_service: 'Awaiting Service',
    manual_attention: 'Manual Attention',
    area_unmatched: 'Unmatched Area',
    qualified: 'Qualified',
    distributed: 'Distributed',
    resolved: 'Resolved',
    inactive: 'Inactive',
    spam: 'Spam',
    closed: 'Closed',
};

export const leadStatusLabels = {
    qualified: 'Qualified',
    area_matched: 'Area Matched',
    available: 'Available',
    claimed: 'Claimed',
    opened: 'Opened',
    contacting: 'Contacting',
    contacted: 'Contacted',
    follow_up: 'Follow Up',
    booked: 'Booked',
    not_interested: 'Not Interested',
    released: 'Released',
    expired: 'Expired',
    lost: 'Lost',
    closed: 'Closed',
    failed: 'Failed',
    new: 'New',
    assigned: 'Assigned',
    unassigned: 'Unassigned',
};

export const statusVariant = (status) => {
    if (['booked', 'resolved', 'qualified', 'distributed', 'available'].includes(status)) return 'success';
    if (['manual_attention', 'area_unmatched', 'failed', 'lost', 'spam'].includes(status)) return 'danger';
    if (['awaiting_customer', 'awaiting_location', 'follow_up', 'released'].includes(status)) return 'warning';
    if (['claimed', 'opened', 'contacting', 'contacted'].includes(status)) return 'info';
    return 'gray';
};

export const getList = (response) => response?.data?.results || response?.data || [];

export const getCount = (response) => response?.data?.count || getList(response).length || 0;

export const formatLabel = (value) => {
    if (!value) return '-';
    return String(value).replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};
