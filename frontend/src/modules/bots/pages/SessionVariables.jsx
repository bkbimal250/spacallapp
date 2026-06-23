import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const SessionVariables = () => (
    <BotResourcePage
        title="Session Variables"
        description="Inspect captured customer choices and runtime variables stored during bot sessions."
        endpoint="getSessionVariables"
        columns={[
            { key: 'session', label: 'Session' },
            { key: 'key', label: 'Key' },
            { key: 'value', label: 'Value' },
            { key: 'created_at', label: 'Created' },
        ]}
    />
);

export default SessionVariables;
