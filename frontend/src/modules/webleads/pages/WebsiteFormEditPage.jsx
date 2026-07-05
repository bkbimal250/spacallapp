import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import LoadingState from '../components/LoadingState';
import WebsiteFormForm from '../components/WebsiteFormForm';
import { getWebsiteForm, updateWebsiteForm } from '../api';

const WebsiteFormEditPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [form, setForm] = useState(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const getErrorMessage = (err) => {
        const data = err?.response?.data;
        if (err?.response?.status === 403) {
            return 'Only admin and super admin users can edit website forms.';
        }
        if (!data) return 'Unable to update website form. Please try again.';
        if (typeof data === 'string') return data;
        if (data.detail) return data.detail;
        return Object.entries(data)
            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
            .join(' | ') || 'Unable to update website form.';
    };

    useEffect(() => {
        getWebsiteForm(id).then((res) => setForm(res.data));
    }, [id]);

    const submit = async (payload) => {
        setSaving(true);
        setError('');
        try {
            await updateWebsiteForm(id, payload);
            navigate(`/web-leads/forms/${id}`);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    };

    if (!form) return <LoadingState label="Loading website form..." />;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-text-primary">Edit Website Form</h1>
                <Link className="text-sm text-primary" to={`/web-leads/forms/${id}`}>Back to detail</Link>
            </div>
            <WebsiteFormForm initialData={form} onSubmit={submit} saving={saving} isEdit submitError={error} />
        </div>
    );
};

export default WebsiteFormEditPage;
