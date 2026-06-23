import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const NodeOptions = () => (
    <BotResourcePage
        title="Node Options"
        description="Inspect button, list, and reply options used to route WhatsApp customers."
        endpoint="getNodeOptions"
        columns={[
            { key: 'label', label: 'Label' },
            { key: 'value', label: 'Value' },
            { key: 'payload_id', label: 'Payload' },
            { key: 'next_node', label: 'Next Node' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default NodeOptions;
