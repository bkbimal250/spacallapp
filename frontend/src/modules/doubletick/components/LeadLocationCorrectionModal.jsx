import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, MapPin, Save, Send } from 'lucide-react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { locationsAPI } from '../../locations/api';
import { branchesAPI } from '../../branches/api';
import { doubletickAPI } from '../api';

const types = [
    ['area', 'Area'],
    ['branch', 'Branch / Spa'],
    ['city', 'City'],
    ['group', 'Location Group'],
    ['greeting', 'Greeting'],
    ['job', 'Job Inquiry'],
    ['not_location', 'Not a Location'],
];

const optionsFrom = (rows = [], labelKey = 'label') => rows.map((row) => ({
    value: row.id,
    label: row[labelKey] || row.name || row.spa_name,
    row,
}));

const LeadLocationCorrectionModal = ({ isOpen, lead, onClose, onSaved }) => {
    const [type, setType] = useState('area');
    const [form, setForm] = useState({ state: '', city: '', group: '', area: '', branch: '', addAlias: true });
    const [states, setStates] = useState([]);
    const [cities, setCities] = useState([]);
    const [groups, setGroups] = useState([]);
    const [areas, setAreas] = useState([]);
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState('');
    const [error, setError] = useState('');

    const conversationId = lead?.conversation;
    const aliasText = lead?.latest_customer_message || lead?.message || '';

    useEffect(() => {
        if (!isOpen) return;
        setError('');
        setLoading('states');
        locationsAPI.getStateOptions()
            .then((response) => setStates(response.data || []))
            .catch(() => setError('Could not load states.'))
            .finally(() => setLoading(''));
    }, [isOpen]);

    useEffect(() => {
        if (!form.state) {
            setCities([]);
            return;
        }
        setLoading('cities');
        locationsAPI.getCityOptions({ state: form.state })
            .then((response) => setCities(response.data || []))
            .catch(() => setError('Could not load cities.'))
            .finally(() => setLoading(''));
    }, [form.state]);

    useEffect(() => {
        if (!form.city) {
            setGroups([]);
            setAreas([]);
            setBranches([]);
            return;
        }
        setLoading('locations');
        Promise.all([
            locationsAPI.getGroupOptions({ city: form.city }),
            locationsAPI.getAreaOptions({ city: form.city }),
        ]).then(([groupResponse, areaResponse]) => {
            setGroups(groupResponse.data || []);
            setAreas(areaResponse.data || []);
        }).catch(() => setError('Could not load groups and areas.'))
            .finally(() => setLoading(''));

        const city = cities.find((item) => item.id === form.city);
        branchesAPI.getBranches({ city: city?.name || '', status: true, page_size: 50 })
            .then((response) => setBranches(response.data?.results || response.data || []))
            .catch(() => setBranches([]));
    }, [form.city, cities]);

    const selected = useMemo(() => ({
        city: cities.find((item) => item.id === form.city),
        group: groups.find((item) => item.id === form.group),
    }), [cities, form.city, form.group, groups]);

    const payload = () => {
        if (type === 'city') return { action: 'correct_city', city_name: selected.city?.name };
        if (type === 'group') return { action: 'correct_group', group_name: selected.group?.name };
        if (type === 'area') return {
            action: 'correct_area',
            area_id: form.area,
            alias_text: aliasText,
            save_alias: form.addAlias,
        };
        if (type === 'branch') return { action: 'correct_branch', branch_id: form.branch };
        if (type === 'greeting') return { action: 'mark_greeting' };
        if (type === 'job') return { action: 'mark_job' };
        return { action: 'mark_not_location' };
    };

    const canSave = ['greeting', 'job', 'not_location'].includes(type)
        || (type === 'city' && form.city)
        || (type === 'group' && form.group)
        || (type === 'area' && form.area)
        || (type === 'branch' && form.branch);
    const canSend = ['area', 'branch'].includes(type) && canSave;

    const save = async (sendToAndroid = false) => {
        if (!conversationId || !canSave) return;
        setLoading(sendToAndroid ? 'send' : 'save');
        setError('');
        try {
            await doubletickAPI.manualCorrect(conversationId, payload());
            if (sendToAndroid) {
                await doubletickAPI.manualCorrect(conversationId, { action: 'save_and_send' });
            }
            await onSaved?.();
            onClose();
        } catch (requestError) {
            setError(requestError.response?.data?.detail || requestError.message || 'Could not save correction.');
        } finally {
            setLoading('');
        }
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Correct Lead Location" maxWidth="max-w-3xl" hideFooter>
            <div className="space-y-5">
                <div className="rounded-lg border border-border bg-background p-4">
                    <p className="text-xs font-semibold uppercase text-text-secondary">Customer message</p>
                    <p className="mt-1 text-sm text-text-primary">{aliasText || 'No customer message available'}</p>
                </div>

                <div>
                    <label className="mb-2 block text-xs font-semibold uppercase text-text-secondary">Correction type</label>
                    <div className="flex flex-wrap gap-2">
                        {types.map(([value, label]) => (
                            <button key={value} type="button" onClick={() => setType(value)}
                                className={`rounded-lg border px-3 py-2 text-sm font-medium ${type === value ? 'border-primary bg-primary text-white' : 'border-border bg-background text-text-secondary hover:text-text-primary'}`}>
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                {!['greeting', 'job', 'not_location'].includes(type) && (
                    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                        <SearchableSelect label="State" placeholder={loading === 'states' ? 'Loading states...' : 'Select state'}
                            options={optionsFrom(states)} value={form.state}
                            onChange={(value) => setForm({ ...form, state: value, city: '', group: '', area: '', branch: '' })} />
                        <SearchableSelect label="City" placeholder={!form.state ? 'Select state first' : loading === 'cities' ? 'Loading cities...' : 'Select city'}
                            options={optionsFrom(cities)} value={form.city}
                            onChange={(value) => setForm({ ...form, city: value, group: '', area: '', branch: '' })} />
                        {['group', 'area', 'branch'].includes(type) && (
                            <SearchableSelect label="Location Group" placeholder={!form.city ? 'Select city first' : 'Optional group'}
                                options={optionsFrom(groups)} value={form.group}
                                onChange={(value) => setForm({ ...form, group: value })} />
                        )}
                        {type === 'area' && (
                            <SearchableSelect label="Area" placeholder={!form.city ? 'Select city first' : loading === 'locations' ? 'Loading areas...' : 'Select area'}
                                options={optionsFrom(areas)} value={form.area}
                                onChange={(value) => setForm({ ...form, area: value })} />
                        )}
                        {type === 'branch' && (
                            <SearchableSelect label="Branch / Spa" placeholder={!form.city ? 'Select city first' : 'Select branch'}
                                options={optionsFrom(branches, 'spa_name')} value={form.branch}
                                onChange={(value) => setForm({ ...form, branch: value })} />
                        )}
                    </div>
                )}

                {type === 'area' && (
                    <label className="flex items-start gap-3 rounded-lg border border-border bg-background p-3">
                        <input type="checkbox" className="mt-1" checked={form.addAlias}
                            onChange={(event) => setForm({ ...form, addAlias: event.target.checked })} />
                        <span>
                            <span className="block text-sm font-medium text-text-primary">Add customer text as an alias</span>
                            <span className="text-xs text-text-secondary">Future messages like “{aliasText || 'this spelling'}” can match automatically.</span>
                        </span>
                    </label>
                )}

                {error && (
                    <div className="flex gap-2 rounded-lg border border-danger/20 bg-danger/10 p-3 text-sm text-danger">
                        <AlertCircle size={17} className="shrink-0" /> {error}
                    </div>
                )}

                <div className="sticky bottom-0 flex flex-wrap justify-end gap-2 border-t border-border bg-card pt-4">
                    <Button variant="secondary" onClick={onClose}>Cancel</Button>
                    <Button variant="secondary" disabled={!canSave} loading={loading === 'save'} onClick={() => save(false)}>
                        <Save size={16} /> Save only
                    </Button>
                    <Button disabled={!canSend} loading={loading === 'send'} onClick={() => save(true)}>
                        <Send size={16} /> Save and Send to Android
                    </Button>
                </div>
                {!canSend && canSave && <p className="text-right text-xs text-warning">Only confirmed area or branch corrections can be sent to Android.</p>}
            </div>
        </Modal>
    );
};

export default LeadLocationCorrectionModal;
