import React, { useEffect, useMemo, useState } from 'react';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';
import WebsiteFormPreview from './WebsiteFormPreview';

const defaults = {
    branch: '',
    website_name: '',
    website_url: '',
    form_title: 'Book Appointment',
    theme: 'light',
    primary_color: '#BD9B5F',
    background_color: '#FFFFFF',
    button_color: '#25D366',
    text_color: '#111111',
    border_radius: '16px',
    font_family: 'Inter',
    submit_button_text: 'Submit',
    success_message: 'Thank you. Our team will contact you shortly.',
    is_active: true,
};

const isColor = (value) => /^#[0-9A-Fa-f]{6}$/.test(value || '');

const WebsiteFormForm = ({ initialData, onSubmit, saving = false, isEdit = false, submitError = '' }) => {
    const [branches, setBranches] = useState([]);
    const [branchesLoading, setBranchesLoading] = useState(true);
    const [branchesError, setBranchesError] = useState('');
    const [form, setForm] = useState(defaults);
    const [errors, setErrors] = useState({});

    useEffect(() => {
        setBranchesLoading(true);
        setBranchesError('');
        branchesAPI.getBranches({ all: true })
            .then((res) => setBranches(res.data.results || res.data || []))
            .catch(() => {
                setBranches([]);
                setBranchesError('Unable to load branches. Please refresh and try again.');
            })
            .finally(() => setBranchesLoading(false));
    }, []);

    useEffect(() => {
        setForm({ ...defaults, ...(initialData || {}) });
    }, [initialData]);

    const branchOptions = useMemo(() => branches.map((branch) => {
        const area = branch.location_area_name || branch.area || '';
        const city = branch.location_city_name || branch.city || '';
        const state = branch.location_state_name || branch.state || '';
        const code = branch.code || '';
        const description = [area, city, state, code].filter(Boolean).join(' | ');

        return {
            value: String(branch.id),
            label: branch.spa_name || branch.name || code || 'Unnamed branch',
            description,
            searchText: [
                branch.spa_name,
                branch.name,
                branch.code,
                branch.area,
                branch.city,
                branch.state,
                branch.location_area_name,
                branch.location_city_name,
                branch.location_state_name,
                branch.location_group_name,
                branch.address,
            ].filter(Boolean).join(' '),
        };
    }), [branches]);

    const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

    const validate = () => {
        const next = {};
        if (!form.branch) next.branch = 'Branch is required.';
        if (!form.website_name.trim()) next.website_name = 'Website name is required.';
        if (!form.form_title.trim()) next.form_title = 'Form title is required.';
        if (!form.submit_button_text.trim()) next.submit_button_text = 'Submit button text is required.';
        if (!form.success_message.trim()) next.success_message = 'Success message is required.';
        try {
            new URL(form.website_url);
        } catch {
            next.website_url = 'Enter a valid website URL.';
        }
        ['primary_color', 'background_color', 'button_color', 'text_color'].forEach((key) => {
            if (!isColor(form[key])) next[key] = 'Use a valid hex color.';
        });
        setErrors(next);
        return Object.keys(next).length === 0;
    };

    const submit = (event) => {
        event.preventDefault();
        if (!validate()) return;
        onSubmit({
            branch: form.branch,
            website_name: form.website_name.trim(),
            website_url: form.website_url.trim(),
            form_title: form.form_title.trim(),
            theme: form.theme,
            primary_color: form.primary_color,
            background_color: form.background_color,
            button_color: form.button_color,
            text_color: form.text_color,
            border_radius: form.border_radius.trim(),
            font_family: form.font_family.trim(),
            submit_button_text: form.submit_button_text.trim(),
            success_message: form.success_message.trim(),
            is_active: Boolean(form.is_active),
        });
    };

    const FieldError = ({ name }) => errors[name] ? <p className="mt-1 text-xs text-danger">{errors[name]}</p> : null;

    return (
        <form onSubmit={submit} className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
            <div className="space-y-5">
                {isEdit && (
                    <div className="rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
                        Old leads keep original website name and URL. Changes apply only to future submissions.
                    </div>
                )}
                {submitError && (
                    <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
                        {submitError}
                    </div>
                )}
                <div className="grid gap-4 md:grid-cols-2">
                    <div>
                        <label className="block text-sm font-medium text-text-primary">Branch/Spa</label>
                        <SearchableSelect
                            className="mt-1"
                            options={branchOptions}
                            value={form.branch || ''}
                            onChange={(value) => update('branch', value)}
                            placeholder={branchesLoading ? 'Loading branches...' : 'Search spa, area, or city'}
                            disabled={branchesLoading || Boolean(branchesError) || branchOptions.length === 0}
                            allowEmpty={false}
                        />
                        {branchesError && <p className="mt-1 text-xs text-danger">{branchesError}</p>}
                        {!branchesLoading && !branchesError && branchOptions.length === 0 && (
                            <p className="mt-1 text-xs text-warning">No branches found for your account.</p>
                        )}
                        <FieldError name="branch" />
                    </div>
                    <label className="text-sm font-medium text-text-primary">Website Name
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.website_name} onChange={(e) => update('website_name', e.target.value)} />
                        <FieldError name="website_name" />
                    </label>
                    <label className="text-sm font-medium text-text-primary md:col-span-2">Website URL
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.website_url} onChange={(e) => update('website_url', e.target.value)} placeholder="https://example.com" />
                        <FieldError name="website_url" />
                    </label>
                    <label className="text-sm font-medium text-text-primary">Form Title
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.form_title} onChange={(e) => update('form_title', e.target.value)} />
                        <FieldError name="form_title" />
                    </label>
                    <label className="text-sm font-medium text-text-primary">Theme
                        <select className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.theme} onChange={(e) => update('theme', e.target.value)}>
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                            <option value="custom">Custom</option>
                        </select>
                    </label>
                    {['primary_color', 'background_color', 'button_color', 'text_color'].map((key) => (
                        <label key={key} className="text-sm font-medium capitalize text-text-primary">{key.replaceAll('_', ' ')}
                            <div className="mt-1 flex gap-2">
                                <input type="color" className="h-10 w-12 rounded border border-border bg-background" value={form[key]} onChange={(e) => update(key, e.target.value)} />
                                <input className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2" value={form[key]} onChange={(e) => update(key, e.target.value)} />
                            </div>
                            <FieldError name={key} />
                        </label>
                    ))}
                    <label className="text-sm font-medium text-text-primary">Border Radius
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.border_radius} onChange={(e) => update('border_radius', e.target.value)} />
                    </label>
                    <label className="text-sm font-medium text-text-primary">Font Family
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.font_family} onChange={(e) => update('font_family', e.target.value)} />
                    </label>
                    <label className="text-sm font-medium text-text-primary">Submit Button Text
                        <input className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" value={form.submit_button_text} onChange={(e) => update('submit_button_text', e.target.value)} />
                        <FieldError name="submit_button_text" />
                    </label>
                    <label className="flex items-center gap-3 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-text-primary">
                        <input type="checkbox" checked={Boolean(form.is_active)} onChange={(e) => update('is_active', e.target.checked)} />
                        Active
                    </label>
                    <label className="text-sm font-medium text-text-primary md:col-span-2">Success Message
                        <textarea className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" rows={3} value={form.success_message} onChange={(e) => update('success_message', e.target.value)} />
                        <FieldError name="success_message" />
                    </label>
                </div>
                <div className="rounded-xl border border-border bg-card p-4">
                    <h3 className="text-sm font-semibold text-text-primary">Fixed customer fields</h3>
                    <div className="mt-3 grid gap-2 text-sm text-text-secondary sm:grid-cols-2">
                        <span>Name required</span>
                        <span>Phone required</span>
                        <span>Address required, max 20</span>
                        <span>Notes optional, max 20</span>
                    </div>
                </div>
                <Button type="submit" loading={saving}>{isEdit ? 'Update Website Form' : 'Create Website Form'}</Button>
            </div>
            <WebsiteFormPreview form={form} />
        </form>
    );
};

export default WebsiteFormForm;
