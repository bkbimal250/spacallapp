import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const Flows = () => (
    <BotResourcePage
        title="Bot Flows"
        description="Manage flow versions, publishing state, and active workflow drafts."
        endpoint="getFlows"
        columns={[
            { key: 'name', label: 'Flow' },
            { key: 'bot_name', label: 'Bot' },
            { key: 'version', label: 'Version' },
            { key: 'is_active', label: 'Active' },
            { key: 'is_published', label: 'Published' },
        ]}
    />
);

export default Flows;
