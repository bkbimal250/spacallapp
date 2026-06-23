import React from 'react';
import BotResourcePage from '../components/BotResourcePage';

const Templates = () => (
    <BotResourcePage
        title="Message Templates"
        description="Manage reusable WhatsApp text and template messages for bot nodes."
        endpoint="getMessageTemplates"
        columns={[
            { key: 'name', label: 'Template' },
            { key: 'language', label: 'Language' },
            { key: 'template_type', label: 'Type' },
            { key: 'text', label: 'Text' },
            { key: 'is_active', label: 'Active' },
        ]}
    />
);

export default Templates;
