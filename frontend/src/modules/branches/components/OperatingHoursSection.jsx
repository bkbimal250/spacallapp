import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Clock, Copy, Save, X } from 'lucide-react';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import { branchesAPI } from '../api';

const weekdays = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
];

const baseTimezoneOptions = [
    'Asia/Kolkata',
    'Asia/Dubai',
    'Asia/Singapore',
    'UTC',
];

const defaultRow = (weekday, timezone = 'Asia/Kolkata') => ({
    weekday,
    weekday_label: weekdays[weekday],
    is_closed: true,
    is_24_hours: false,
    opens_at: '',
    closes_at: '',
    timezone,
    is_active: true,
    is_overnight: false,
});

const normalizeTime = (value) => (value ? String(value).slice(0, 5) : '');

const toFormRows = (rows = [], timezone = 'Asia/Kolkata') => {
    const byWeekday = new Map(rows.map((row) => [row.weekday, row]));
    return weekdays.map((_, weekday) => {
        const row = byWeekday.get(weekday);
        return row
            ? {
                ...row,
                opens_at: normalizeTime(row.opens_at),
                closes_at: normalizeTime(row.closes_at),
                timezone: row.timezone || timezone,
            }
            : defaultRow(weekday, timezone);
    });
};

const formatTime = (value) => {
    if (!value) return '';
    const [hourPart, minutePart] = value.split(':');
    const hour = Number(hourPart);
    const minute = Number(minutePart || 0);
    const suffix = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${String(minute).padStart(2, '0')} ${suffix}`;
};

const scheduleLabel = (row) => {
    if (row.is_closed) return 'Closed';
    if (row.is_24_hours) return '24 Hours';
    if (!row.opens_at || !row.closes_at) return 'Not configured';
    return `${formatTime(normalizeTime(row.opens_at))} -> ${formatTime(normalizeTime(row.closes_at))}`;
};

const buildPayloadRow = (row, timezone) => {
    const mode = row.is_closed ? 'closed' : row.is_24_hours ? '24_hours' : 'open';
    return {
        weekday: row.weekday,
        is_closed: mode === 'closed',
        is_24_hours: mode === '24_hours',
        opens_at: mode === 'open' ? row.opens_at : null,
        closes_at: mode === 'open' ? row.closes_at : null,
        timezone: row.timezone || timezone,
        is_active: true,
    };
};

const OperatingHoursSection = ({ branch, canEdit = false, onConfiguredChange }) => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [serverRows, setServerRows] = useState([]);
    const [formRows, setFormRows] = useState([]);
    const [timezone, setTimezone] = useState('Asia/Kolkata');
    const [editing, setEditing] = useState(false);
    const [dirty, setDirty] = useState(false);
    const [validationErrors, setValidationErrors] = useState({});

    const configuredCount = useMemo(
        () => serverRows.filter((row) => row.id || !row.is_closed || row.is_24_hours).length,
        [serverRows]
    );
    const timezoneChoices = useMemo(
        () => Array.from(new Set([timezone, ...baseTimezoneOptions].filter(Boolean))),
        [timezone]
    );

    const loadHours = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const response = await branchesAPI.getOperatingHours(branch.id);
            const nextTimezone = response.data?.timezone || 'Asia/Kolkata';
            const rows = toFormRows(response.data?.operating_hours || [], nextTimezone);
            setTimezone(nextTimezone);
            setServerRows(rows);
            setFormRows(rows);
            setDirty(false);
            setValidationErrors({});
            onConfiguredChange?.(rows.filter((row) => row.id).length);
        } catch (err) {
            console.error('Failed to load operating hours', err);
            setError('Could not load operating hours.');
        } finally {
            setLoading(false);
        }
    }, [branch.id, onConfiguredChange]);

    useEffect(() => {
        loadHours();
    }, [loadHours]);

    useEffect(() => {
        if (!dirty) return undefined;
        const onBeforeUnload = (event) => {
            event.preventDefault();
            event.returnValue = '';
        };
        window.addEventListener('beforeunload', onBeforeUnload);
        return () => window.removeEventListener('beforeunload', onBeforeUnload);
    }, [dirty]);

    const markDirty = (rows) => {
        setFormRows(rows);
        setDirty(true);
        setSuccess('');
    };

    const setMode = (weekday, mode) => {
        markDirty(formRows.map((row) => {
            if (row.weekday !== weekday) return row;
            return {
                ...row,
                is_closed: mode === 'closed',
                is_24_hours: mode === '24_hours',
                opens_at: mode === 'open' ? row.opens_at : '',
                closes_at: mode === 'open' ? row.closes_at : '',
            };
        }));
    };

    const setTime = (weekday, key, value) => {
        markDirty(formRows.map((row) => (row.weekday === weekday ? { ...row, [key]: value } : row)));
    };

    const copyMondayToAll = () => {
        const monday = formRows[0];
        markDirty(formRows.map((row) => ({
            ...row,
            is_closed: monday.is_closed,
            is_24_hours: monday.is_24_hours,
            opens_at: monday.opens_at,
            closes_at: monday.closes_at,
            timezone,
        })));
    };

    const copyMondayToWeekdays = () => {
        const monday = formRows[0];
        markDirty(formRows.map((row) => (
            row.weekday > 0 && row.weekday < 5
                ? { ...row, is_closed: monday.is_closed, is_24_hours: monday.is_24_hours, opens_at: monday.opens_at, closes_at: monday.closes_at, timezone }
                : row
        )));
    };

    const validate = () => {
        const nextErrors = {};
        formRows.forEach((row) => {
            if (!row.is_closed && !row.is_24_hours) {
                if (!row.opens_at || !row.closes_at) {
                    nextErrors[row.weekday] = 'Opening and closing time are required.';
                } else if (row.opens_at === row.closes_at) {
                    nextErrors[row.weekday] = 'Opening and closing time cannot be the same.';
                }
            }
        });
        setValidationErrors(nextErrors);
        return Object.keys(nextErrors).length === 0;
    };

    const save = async () => {
        if (!validate()) return;
        setSaving(true);
        setError('');
        try {
            const payload = {
                timezone,
                operating_hours: formRows.map((row) => buildPayloadRow(row, timezone)),
            };
            const response = await branchesAPI.updateOperatingHours(branch.id, payload);
            const nextTimezone = response.data?.timezone || timezone;
            const rows = toFormRows(response.data?.operating_hours || [], nextTimezone);
            setTimezone(nextTimezone);
            setServerRows(rows);
            setFormRows(rows);
            setEditing(false);
            setDirty(false);
            setValidationErrors({});
            setSuccess('Operating hours updated successfully.');
            onConfiguredChange?.(rows.filter((row) => row.id).length);
        } catch (err) {
            console.error('Failed to save operating hours', err);
            const detail = err.response?.data?.detail || err.response?.data?.error || 'Could not save operating hours.';
            setError(typeof detail === 'string' ? detail : 'Could not save operating hours.');
        } finally {
            setSaving(false);
        }
    };

    const closeEditor = () => {
        if (dirty && !window.confirm('Your operating hours changes have not been saved. Discard them?')) return;
        setFormRows(serverRows);
        setDirty(false);
        setEditing(false);
        setValidationErrors({});
        setError('');
    };

    const changeTimezone = (value) => {
        setTimezone(value);
        markDirty(formRows.map((row) => ({ ...row, timezone: value })));
    };

    return (
        <section className="bg-card border border-border rounded-lg">
            <div className="flex flex-col gap-3 border-b border-border px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-primary"><Clock size={18} /></span>
                    <div>
                        <h2 className="text-base font-semibold text-text-primary">Operating Hours</h2>
                        <p className="text-xs text-text-secondary">Timezone: {timezone}</p>
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={configuredCount ? 'success' : 'warning'}>{configuredCount ? 'Configured' : 'Not Configured'}</Badge>
                    {canEdit && !editing && (
                        <Button size="sm" onClick={() => setEditing(true)}>
                            {configuredCount ? 'Edit Operating Hours' : 'Create Operating Hours'}
                        </Button>
                    )}
                </div>
            </div>

            <div className="space-y-4 p-5">
                {error && (
                    <div className="flex gap-2 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                        <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                        {error}
                    </div>
                )}
                {success && (
                    <div className="rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
                        {success}
                    </div>
                )}

                <div className="rounded-lg border border-info/20 bg-info/10 p-4">
                    <h3 className="text-sm font-semibold text-text-primary">Routing Impact</h3>
                    <p className="mt-1 text-sm text-text-secondary">
                        These operating hours are used by Call Routing to determine whether this spa is open when a customer enquiry is received.
                        Historical routing requests keep their original source-status snapshot.
                    </p>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-text-secondary">Loading operating hours...</div>
                ) : editing ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 gap-3 lg:grid-cols-[260px_1fr] lg:items-end">
                            <label className="block">
                                <span className="mb-1 block text-sm font-medium text-text-secondary">Timezone</span>
                                <select
                                    value={timezone}
                                    onChange={(event) => changeTimezone(event.target.value)}
                                    className="block w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
                                >
                                    {timezoneChoices.map((option) => <option key={option} value={option}>{option}</option>)}
                                </select>
                            </label>
                            <div className="flex flex-wrap gap-2">
                                <Button variant="secondary" size="sm" className="gap-2" onClick={copyMondayToWeekdays}>
                                    <Copy size={15} />
                                    Copy Monday to weekdays
                                </Button>
                                <Button variant="secondary" size="sm" className="gap-2" onClick={copyMondayToAll}>
                                    <Copy size={15} />
                                    Copy Monday to all days
                                </Button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-3">
                            {formRows.map((row) => (
                                <EditorRow
                                    key={row.weekday}
                                    row={row}
                                    error={validationErrors[row.weekday]}
                                    setMode={setMode}
                                    setTime={setTime}
                                />
                            ))}
                        </div>

                        <div className="flex flex-col gap-2 border-t border-border pt-4 sm:flex-row sm:justify-end">
                            <Button variant="secondary" className="gap-2" onClick={closeEditor}>
                                <X size={16} />
                                Discard
                            </Button>
                            <Button className="gap-2" loading={saving} onClick={save}>
                                <Save size={16} />
                                Save Operating Hours
                            </Button>
                        </div>
                    </div>
                ) : (
                    <ScheduleTable rows={serverRows} />
                )}
            </div>
        </section>
    );
};

const ScheduleTable = ({ rows }) => (
    <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-sm">
            <thead>
                <tr className="text-left text-xs font-semibold uppercase text-text-secondary">
                    <th className="px-3 py-2">Day</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Schedule</th>
                    <th className="px-3 py-2">Note</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-border">
                {rows.map((row) => (
                    <tr key={row.weekday}>
                        <td className="px-3 py-3 font-medium text-text-primary">{row.weekday_label || weekdays[row.weekday]}</td>
                        <td className="px-3 py-3">
                            <Badge variant={row.is_closed ? 'warning' : 'success'}>{row.is_closed ? 'Closed' : row.is_24_hours ? '24 Hours' : 'Open'}</Badge>
                        </td>
                        <td className="px-3 py-3 text-text-primary">{scheduleLabel(row)}</td>
                        <td className="px-3 py-3 text-text-secondary">{row.is_overnight ? 'Overnight / next day' : ''}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

const EditorRow = ({ row, error, setMode, setTime }) => {
    const mode = row.is_closed ? 'closed' : row.is_24_hours ? '24_hours' : 'open';
    const mayBeOvernight = mode === 'open' && row.opens_at && row.closes_at && row.opens_at > row.closes_at;

    return (
        <div className="rounded-lg border border-border bg-background p-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[160px_minmax(240px,1fr)_160px_160px] lg:items-start">
                <div>
                    <p className="font-semibold text-text-primary">{row.weekday_label || weekdays[row.weekday]}</p>
                    {mayBeOvernight && <p className="mt-1 text-xs font-medium text-info">Overnight / next day</p>}
                </div>

                <fieldset className="flex flex-wrap gap-3">
                    <legend className="sr-only">{row.weekday_label} operating mode</legend>
                    {[
                        ['open', 'Open'],
                        ['closed', 'Closed'],
                        ['24_hours', '24 Hours'],
                    ].map(([value, label]) => (
                        <label key={value} className="inline-flex items-center gap-2 text-sm text-text-primary">
                            <input
                                type="radio"
                                name={`hours-mode-${row.weekday}`}
                                value={value}
                                checked={mode === value}
                                onChange={() => setMode(row.weekday, value)}
                            />
                            {label}
                        </label>
                    ))}
                </fieldset>

                <label className="block">
                    <span className="mb-1 block text-xs font-medium text-text-secondary">Opens</span>
                    <input
                        type="time"
                        value={row.opens_at || ''}
                        disabled={mode !== 'open'}
                        onChange={(event) => setTime(row.weekday, 'opens_at', event.target.value)}
                        className="block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary disabled:opacity-50"
                    />
                </label>

                <label className="block">
                    <span className="mb-1 block text-xs font-medium text-text-secondary">Closes</span>
                    <input
                        type="time"
                        value={row.closes_at || ''}
                        disabled={mode !== 'open'}
                        onChange={(event) => setTime(row.weekday, 'closes_at', event.target.value)}
                        className="block w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary disabled:opacity-50"
                    />
                </label>
            </div>
            {error && <p className="mt-2 text-xs text-danger">{error}</p>}
        </div>
    );
};

export default OperatingHoursSection;
