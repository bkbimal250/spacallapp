export const getList = (response) => response?.data?.results || response?.data || [];

export const getCount = (response) => response?.data?.count || getList(response).length || 0;

export const formatLabel = (value) => {
    if (!value) return '-';
    return String(value).replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};

export const botTypeLabels = {
    booking: 'Booking',
    job: 'Job Inquiry',
    support: 'Support',
    follow_up: 'Follow Up',
    branch: 'Branch Specific',
    city: 'City Specific',
    generic: 'Generic',
};

export const nodeTypeGroups = [
    {
        label: 'Messages',
        items: ['start', 'text_message', 'template_message', 'question', 'option_buttons', 'interactive_list'],
    },
    {
        label: 'Location',
        items: ['dynamic_state_select', 'dynamic_city_select', 'dynamic_area_select', 'dynamic_branch_select', 'match_location'],
    },
    {
        label: 'Lead Actions',
        items: ['assign_lead', 'broadcast_lead', 'round_robin_assign', 'manual_handover', 'tag_lead', 'update_lead_status'],
    },
    {
        label: 'Automation',
        items: ['condition', 'collect_input', 'api_call', 'google_sheet_append', 'delay', 'fallback', 'end'],
    },
];

export const statusVariant = (status) => {
    if (['active', 'sent', 'completed', 'success', 'published'].includes(status)) return 'success';
    if (['handed_over', 'failed', 'expired'].includes(status)) return 'danger';
    if (['started', 'skipped', 'queued'].includes(status)) return 'warning';
    return 'info';
};

export const emptyBot = {
    name: '',
    slug: '',
    bot_type: 'booking',
    default_language: 'en',
    priority: 0,
    is_active: true,
    description: '',
    config: {},
};

export const emptyNode = {
    name: '',
    node_type: 'text_message',
    message_text: '',
    language: '',
    config: {},
    position: 0,
    order: 0,
    is_active: true,
    default_next_node: '',
};
