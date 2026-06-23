import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const Transitions = () => (
    <BotResourcePage
        title="Bot Transitions"
        description="Review conditional route links between workflow nodes."
        endpoint="getTransitions"
        columns={[
            { key: 'from_node', label: 'From Node' },
            { key: 'to_node', label: 'To Node' },
            { key: 'condition', label: 'Condition' },
            { key: 'priority', label: 'Priority' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default Transitions;
