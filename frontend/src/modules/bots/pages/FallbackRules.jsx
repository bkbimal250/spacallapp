import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const FallbackRules = () => (
    <BotResourcePage
        title="Fallback Rules"
        description="Control retry messages, fallback routing, and handover thresholds."
        endpoint="getFallbackRules"
        columns={[
            { key: 'name', label: 'Rule' },
            { key: 'retry_number', label: 'Retry' },
            { key: 'message_text', label: 'Message' },
            { key: 'next_node', label: 'Next Node' },
            { key: 'handover_after', label: 'Handover After' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default FallbackRules;
