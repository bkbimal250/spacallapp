import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../../../shared/components/Button';
import CopyButton from '../components/CopyButton';
import WebsiteFormForm from '../components/WebsiteFormForm';
import WebsiteFormIntegrationCode from '../components/WebsiteFormIntegrationCode';
import { createWebsiteForm } from '../api';

const WebsiteFormCreatePage = () => {
    const navigate = useNavigate();
    const [saving, setSaving] = useState(false);
    const [created, setCreated] = useState(null);
    const [error, setError] = useState('');

    const getErrorMessage = (err) => {
        const data = err?.response?.data;
        if (err?.response?.status === 403) {
            return 'Only admin and super admin users can create website forms.';
        }
        if (!data) return 'Unable to create website form. Please try again.';
        if (typeof data === 'string') return data;
        if (data.detail) return data.detail;
        return Object.entries(data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join(' | ') || 'Unable to create website form.';
    };

    const submit = async (payload) => {
        setSaving(true);
        setError('');
        try {
            const res = await createWebsiteForm(payload);
            setCreated(res.data);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-text-primary">Create Website Form</h1>
                <Link className="text-sm text-primary" to="/web-leads/forms">Back to forms</Link>
            </div>
            {created ? (
                <div className="space-y-5 rounded-xl border border-border bg-card p-5">
                    <div className="flex flex-wrap items-center gap-3">
                        <h2 className="text-lg font-semibold text-text-primary">Generated Form Key</h2>
                        <code className="rounded bg-primary/10 px-3 py-1 text-primary">{created.form_key}</code>
                        <CopyButton value={created.form_key} label="Copy form key" />
                    </div>
                    <WebsiteFormIntegrationCode form={created} />
                    <div className="flex gap-2">
                        <Button onClick={() => navigate(`/web-leads/forms/${created.id}`)}>Open Detail Page</Button>
                        <Button variant="secondary" onClick={() => setCreated(null)}>Create Another</Button>
                    </div>
                </div>
            ) : (
                <WebsiteFormForm onSubmit={submit} saving={saving} submitError={error} />
            )}
        </div>
    );
};

export default WebsiteFormCreatePage;
