import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const SheetSyncLogs = () => (
    <BotResourcePage
        title="Sheet Sync Logs"
        description="Audit Google Sheet append and sync work performed by bot nodes."
        endpoint="getSheetSyncLogs"
        columns={[
            { key: 'integration', label: 'Integration' },
            { key: 'lead', label: 'Lead' },
            { key: 'success', label: 'Success' },
            { key: 'error_message', label: 'Error' },
            { key: 'created_at', label: 'Created' },
        ]}
    />
);

export default SheetSyncLogs;
