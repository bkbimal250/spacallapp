import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const HandoverRules = () => (
    <BotResourcePage
        title="Handover Rules"
        description="Configure when unresolved bot conversations move to a branch or team member."
        endpoint="getHandoverRules"
        columns={[
            { key: 'name', label: 'Rule' },
            { key: 'condition', label: 'Condition' },
            { key: 'assign_user', label: 'User' },
            { key: 'assign_branch', label: 'Branch' },
            { key: 'priority', label: 'Priority' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default HandoverRules;
