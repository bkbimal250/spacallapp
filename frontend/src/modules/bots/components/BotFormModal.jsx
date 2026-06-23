import React, { useEffect, useMemo, useState } from 'react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import { botTypeLabels, emptyBot, formatLabel } from '../utils';

const triggerTypes = [
    'first_inbound',
    'keyword',
    'lead_created',
    'location_missing',
    'area_matched',
    'manual_action',
    'status_changed',
    'follow_up_due',
    'abandoned',
    'campaign_source',
    'channel',
];

const slugify = (value) => String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

const createDefaultForm = () => ({
    ...emptyBot,
    trigger_type: 'first_inbound',
    is_default_trigger: true,
    trigger_priority: 0,
    channel: '',
    keywords: '',
    source_campaign: '',
    city: '',
    lead_type: '',
});

const BotFormModal = ({ isOpen, onClose, onSubmit, submitting = false, error = '', success = '' }) => {
    const [form, setForm] = useState(createDefaultForm);

    useEffect(() => {
        if (isOpen) {
            const timer = window.setTimeout(() => setForm(createDefaultForm()), 0);
            return () => window.clearTimeout(timer);
        }
        return undefined;
    }, [isOpen]);

    const botTypeOptions = useMemo(() => Object.entries(botTypeLabels), []);

    const update = (key, value) => {
        setForm((current) => {
            const next = { ...current, [key]: value };
            if (key === 'name' && !current.slug) {
                next.slug = slugify(value);
            }
            return next;
        });
    };

    const submit = (event) => {
        event.preventDefault();
        onSubmit?.(form);
    };

    return (
        <Modal isOpen={isOpen} onClose={submitting ? undefined : onClose} title="Create Bot">
            <form onSubmit={submit} className="space-y-5">
                {success && (
                    <div className="rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
                        {success}
                    </div>
                )}
                {error && (
                    <div className="rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                        label="Bot Name"
                        value={form.name}
                        onChange={(event) => update('name', event.target.value)}
                        placeholder="Booking Bot"
                        required
                    />
                    <Input
                        label="Slug"
                        value={form.slug}
                        onChange={(event) => update('slug', slugify(event.target.value))}
                        placeholder="booking-bot"
                        required
                    />
                    <label>
                        <span className="block text-sm font-medium text-text-secondary mb-1">Bot Type</span>
                        <select
                            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
                            value={form.bot_type}
                            onChange={(event) => update('bot_type', event.target.value)}
                        >
                            {botTypeOptions.map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                    </label>
                    <Input
                        label="Default Language"
                        value={form.default_language}
                        onChange={(event) => update('default_language', event.target.value)}
                        placeholder="en"
                    />
                    <Input
                        label="Priority"
                        type="number"
                        value={form.priority}
                        onChange={(event) => update('priority', event.target.value)}
                    />
                    <label className="flex items-center gap-2 mt-7">
                        <input
                            type="checkbox"
                            checked={Boolean(form.is_active)}
                            onChange={(event) => update('is_active', event.target.checked)}
                        />
                        <span className="text-sm text-text-primary">Bot active</span>
                    </label>
                </div>

                <label>
                    <span className="block text-sm font-medium text-text-secondary mb-1">Description</span>
                    <textarea
                        className="w-full min-h-[90px] bg-background border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-primary resize-none"
                        value={form.description}
                        onChange={(event) => update('description', event.target.value)}
                        placeholder="Describe when this bot should handle WhatsApp leads."
                    />
                </label>

                <div className="rounded-lg border border-border bg-background p-4 space-y-4">
                    <div>
                        <p className="font-semibold text-text-primary">Trigger Setup</p>
                        <p className="text-xs text-text-secondary">Optional trigger is created after bot save using the existing bot trigger API.</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <label>
                            <span className="block text-sm font-medium text-text-secondary mb-1">Trigger</span>
                            <select
                                className="w-full px-3 py-2 rounded-lg border border-border bg-card text-sm"
                                value={form.trigger_type}
                                onChange={(event) => update('trigger_type', event.target.value)}
                            >
                                {triggerTypes.map((type) => (
                                    <option key={type} value={type}>{formatLabel(type)}</option>
                                ))}
                            </select>
                        </label>
                        <Input
                            label="Channel ID"
                            value={form.channel}
                            onChange={(event) => update('channel', event.target.value)}
                            placeholder="Optional WABA channel UUID"
                        />
                        <Input
                            label="Keywords"
                            value={form.keywords}
                            onChange={(event) => update('keywords', event.target.value)}
                            placeholder="booking, massage, spa"
                        />
                        <Input
                            label="Source Campaign"
                            value={form.source_campaign}
                            onChange={(event) => update('source_campaign', event.target.value)}
                            placeholder="Optional campaign"
                        />
                        <Input
                            label="City"
                            value={form.city}
                            onChange={(event) => update('city', event.target.value)}
                            placeholder="Optional city"
                        />
                        <Input
                            label="Lead Type"
                            value={form.lead_type}
                            onChange={(event) => update('lead_type', event.target.value)}
                            placeholder="booking / job / support"
                        />
                        <Input
                            label="Trigger Priority"
                            type="number"
                            value={form.trigger_priority}
                            onChange={(event) => update('trigger_priority', event.target.value)}
                        />
                        <label className="flex items-center gap-2 mt-7">
                            <input
                                type="checkbox"
                                checked={Boolean(form.is_default_trigger)}
                                onChange={(event) => update('is_default_trigger', event.target.checked)}
                            />
                            <span className="text-sm text-text-primary">Default trigger</span>
                        </label>
                    </div>
                </div>

                <div className="flex justify-end gap-2 border-t border-border pt-4">
                    <Button type="button" variant="secondary" disabled={submitting} onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit" loading={submitting} disabled={submitting || !form.name.trim() || !form.slug.trim()}>
                        Create Bot
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default BotFormModal;
