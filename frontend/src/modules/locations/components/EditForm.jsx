import React, { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Modal from '../../../shared/components/Modal';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { toOptions } from '../utils';

const entityLabels = {
    state: 'State',
    city: 'City',
    area: 'Area',
    group: 'Location group',
};

const getInitialValues = (type, record) => ({
    name: record.name || '',
    country: record.country || 'India',
    code: record.code || '',
    state: record.state || record.state_detail?.id || '',
    city: record.city || record.city_detail?.id || '',
    description: record.description || '',
    is_active: record.is_active !== false,
    priority: record.priority ?? 0,
});

const EditForm = ({ record, type, states = [], cities = [], saving = false, error = '', onClose, onSubmit }) => {
    const [form, setForm] = useState(() => getInitialValues(type, record));
    const label = entityLabels[type];

    useEffect(() => {
        setForm(getInitialValues(type, record));
    }, [type, record]);

    const updateForm = (field, value) => {
        setForm((current) => ({ ...current, [field]: value }));
    };

    const handleSubmit = (event) => {
        event.preventDefault();

        const payload = {
            name: form.name.trim(),
            is_active: form.is_active,
            priority: Number(form.priority || 0),
        };

        if (type === 'state') {
            payload.country = form.country.trim();
            payload.code = form.code.trim() || null;
        } else if (type === 'city') {
            payload.state = form.state;
        } else if (type === 'area') {
            payload.city = form.city;
        } else if (type === 'group') {
            payload.city = form.city;
            payload.description = form.description.trim() || null;
        }

        onSubmit(payload);
    };

    const cityOptions = toOptions(cities, (city) => (
        `${city.name}${city.state_name ? `, ${city.state_name}` : ''}`
    ));

    return (
        <Modal
            isOpen={Boolean(record)}
            onClose={saving ? undefined : onClose}
            title={`Edit ${label}`}
            maxWidth="max-w-2xl"
            hideFooter
        >
            <form onSubmit={handleSubmit} className="space-y-5">
                <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
                    <p className="text-sm font-semibold text-text-primary">Update {label.toLowerCase()} details</p>
                    <p className="mt-1 text-xs text-text-secondary">
                        Changes are saved to the location record and its parent relationship.
                    </p>
                </div>

                {type === 'state' && (
                    <div className="grid gap-4 sm:grid-cols-2">
                        <Input
                            label="Country"
                            value={form.country}
                            onChange={(event) => updateForm('country', event.target.value)}
                            placeholder="India"
                            maxLength={120}
                            required
                        />
                        <Input
                            label="State name"
                            value={form.name}
                            onChange={(event) => updateForm('name', event.target.value)}
                            placeholder="Maharashtra"
                            maxLength={120}
                            required
                        />
                        <Input
                            label="State code"
                            value={form.code}
                            onChange={(event) => updateForm('code', event.target.value)}
                            placeholder="MH"
                            maxLength={20}
                        />
                        <Input
                            label="Priority"
                            type="number"
                            value={form.priority}
                            onChange={(event) => updateForm('priority', event.target.value)}
                            min="0"
                            step="1"
                        />
                    </div>
                )}

                {type === 'city' && (
                    <div className="space-y-4">
                        <SearchableSelect
                            label="Parent state"
                            options={toOptions(states, (state) => `${state.name}${state.country ? `, ${state.country}` : ''}`)}
                            value={form.state}
                            onChange={(value) => updateForm('state', value)}
                            placeholder="Select a state"
                        />
                        <div className="grid gap-4 sm:grid-cols-2">
                            <Input
                                label="City name"
                                value={form.name}
                                onChange={(event) => updateForm('name', event.target.value)}
                                placeholder="Bengaluru"
                                maxLength={120}
                                required
                            />
                            <Input
                                label="Priority"
                                type="number"
                                value={form.priority}
                                onChange={(event) => updateForm('priority', event.target.value)}
                                min="0"
                                step="1"
                            />
                        </div>
                    </div>
                )}

                {type === 'area' && (
                    <div className="space-y-4">
                        <SearchableSelect
                            label="Parent city"
                            options={cityOptions}
                            value={form.city}
                            onChange={(value) => updateForm('city', value)}
                            placeholder="Select a city"
                        />
                        <div className="grid gap-4 sm:grid-cols-2">
                            <Input
                                label="Area name"
                                value={form.name}
                                onChange={(event) => updateForm('name', event.target.value)}
                                placeholder="Indiranagar"
                                maxLength={140}
                                required
                            />
                            <Input
                                label="Priority"
                                type="number"
                                value={form.priority}
                                onChange={(event) => updateForm('priority', event.target.value)}
                                min="0"
                                step="1"
                            />
                        </div>
                    </div>
                )}

                {type === 'group' && (
                    <div className="space-y-4">
                        <SearchableSelect
                            label="Parent city"
                            options={cityOptions}
                            value={form.city}
                            onChange={(value) => updateForm('city', value)}
                            placeholder="Select a city"
                        />
                        <div className="grid gap-4 sm:grid-cols-2">
                            <Input
                                label="Group name"
                                value={form.name}
                                onChange={(event) => updateForm('name', event.target.value)}
                                placeholder="North Bengaluru"
                                maxLength={160}
                                required
                            />
                            <Input
                                label="Priority"
                                type="number"
                                value={form.priority}
                                onChange={(event) => updateForm('priority', event.target.value)}
                                min="0"
                                step="1"
                            />
                        </div>
                        <div>
                            <label className="mb-1 block text-sm font-medium text-text-secondary">Description</label>
                            <textarea
                                value={form.description}
                                onChange={(event) => updateForm('description', event.target.value)}
                                placeholder="Optional notes for this location group"
                                className="min-h-24 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                    </div>
                )}

                <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-border bg-background px-4 py-3">
                    <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(event) => updateForm('is_active', event.target.checked)}
                        className="h-4 w-4 accent-primary"
                    />
                    <span>
                        <span className="block text-sm font-medium text-text-primary">Active</span>
                        <span className="block text-xs text-text-secondary">Inactive locations are excluded from active options.</span>
                    </span>
                </label>

                {error && (
                    <p role="alert" className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                        {error}
                    </p>
                )}

                <div className="flex justify-end gap-2 border-t border-border pt-4">
                    <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        loading={saving}
                        disabled={!form.name.trim() || (type === 'state' && !form.country.trim()) || (type === 'city' && !form.state) || ((type === 'area' || type === 'group') && !form.city)}
                        className="gap-2"
                    >
                        <Save size={16} />
                        Save changes
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default EditForm;