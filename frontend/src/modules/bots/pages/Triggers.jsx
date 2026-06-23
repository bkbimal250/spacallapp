import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const Triggers = () => (
    <BotResourcePage
        title="Bot Triggers"
        description="Control which bots start from WhatsApp keywords, channels, cities, campaigns, or defaults."
        endpoint="getTriggers"
        columns={[
            { key: 'bot_name', label: 'Bot' },
            { key: 'trigger_type', label: 'Trigger' },
            { key: 'keywords', label: 'Keywords' },
            { key: 'channel_name', label: 'Channel' },
            { key: 'is_default', label: 'Default' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default Triggers;
