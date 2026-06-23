import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const Nodes = () => (
    <BotResourcePage
        title="Bot Nodes"
        description="Review every workflow node, message prompt, order, and node type."
        endpoint="getNodes"
        columns={[
            { key: 'name', label: 'Node' },
            { key: 'node_type', label: 'Type' },
            { key: 'message_text', label: 'Message' },
            { key: 'order', label: 'Order' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default Nodes;
