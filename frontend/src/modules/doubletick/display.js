import { formatDate } from '../../shared/utils/formatDate';
import { formatLabel } from './utils';

export const emptyText = '-';

export const pickText = (...values) => {
    const value = values.find((item) => item !== null && item !== undefined && String(item).trim() !== '');
    return value === undefined ? emptyText : String(value);
};

export const customerName = (record = {}) => pickText(record.customer_name, record.whatsapp_name, record.phone_number, 'Unknown customer');

export const customerPhone = (record = {}) => pickText(record.phone_number, record.normalized_phone);

export const leadLocation = (record = {}) => pickText(
    record.city,
    record.raw_city,
    record.matched_area_name,
    record.area,
    record.raw_area
);

export const leadArea = (record = {}) => pickText(record.matched_area_name, record.area, record.raw_area);

export const leadBranch = (record = {}) => pickText(record.current_branch_name, record.assigned_branch_name, record.branch_name);

export const leadOwner = (record = {}) => pickText(record.current_user_name, record.assigned_user_name, record.assigned_device_name, 'Unclaimed');

export const leadMessage = (record = {}) => pickText(record.latest_customer_message, record.initial_message, record.message);

export const leadTime = (record = {}) => {
    const value = record.last_message_at || record.last_customer_message_at || record.distributed_at || record.created_at || record.received_at;
    return value ? formatDate(value, 'MMM dd, HH:mm') : emptyText;
};

export const pendingReason = (record = {}) => {
    if (record.requires_manual_attention) return 'Manual attention required';
    return formatLabel(record.pending_reason || record.status || 'Pending');
};

export const wabaNumber = (record = {}) => pickText(record.channel_waba_number, record.waba_number, record.channel);

export const sourceLabel = (record = {}) => pickText(record.source_ad, record.campaign, record.source, record.raw_service, 'WhatsApp');
