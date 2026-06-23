import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const ApiCallLogs = () => (
    <BotResourcePage
        title="API Call Logs"
        description="Audit external webhook and API calls made by bot automation nodes."
        endpoint="getApiCallLogs"
        columns={[
            { key: 'url', label: 'URL' },
            { key: 'method', label: 'Method' },
            { key: 'status_code', label: 'Status' },
            { key: 'success', label: 'Success' },
            { key: 'error_message', label: 'Error' },
            { key: 'created_at', label: 'Created' },
        ]}
    />
);

export default ApiCallLogs;
