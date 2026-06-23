import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const DataSources = () => (
    <BotResourcePage
        title="Bot Data Sources"
        description="Review database-backed sources used by city, area, branch, and matching nodes."
        endpoint="getDataSources"
        columns={[
            { key: 'name', label: 'Source' },
            { key: 'source_type', label: 'Type' },
            { key: 'config', label: 'Config' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default DataSources;
