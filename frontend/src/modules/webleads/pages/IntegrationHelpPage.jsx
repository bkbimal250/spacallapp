import React from 'react';
import WebsiteFormIntegrationCode from '../components/WebsiteFormIntegrationCode';

const IntegrationHelpPage = () => (
    <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-text-primary">Website Lead Integration Help</h1>
        <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="mb-4 text-lg font-semibold text-text-primary">HTML Widget Install</h2>
            <WebsiteFormIntegrationCode form={{ form_key: 'FORM_KEY', theme: 'dark', primary_color: '#BD9B5F', button_color: '#25D366', border_radius: '20' }} />
        </section>
        <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="mb-3 text-lg font-semibold text-text-primary">Customer Fields</h2>
            <div className="grid gap-2 text-sm text-text-secondary sm:grid-cols-2">
                <span>Name required</span>
                <span>Phone required</span>
                <span>Address required, max 20 characters</span>
                <span>Notes optional, max 20 characters</span>
            </div>
        </section>
        <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="mb-3 text-lg font-semibold text-text-primary">Important Rules</h2>
            <ul className="space-y-2 text-sm text-text-secondary">
                <li>Do not send branch from frontend.</li>
                <li>Do not send website_name from frontend.</li>
                <li>Do not send website_url from frontend.</li>
                <li>Backend identifies everything using form_key.</li>
                <li>Every website should have its own form_key.</li>
                <li>One branch can have 10+ websites.</li>
                <li>Customer fields are fixed: name, phone, address, notes.</li>
            </ul>
        </section>
    </div>
);

export default IntegrationHelpPage;
