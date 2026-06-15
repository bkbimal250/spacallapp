import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { MapPin, Plus, RefreshCw, Save, Settings2, Trash2 } from 'lucide-react';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Table from '../../../shared/components/Table';
import { doubletickAPI } from '../api';
import { getList } from '../utils';
import DoubleTickTabs from '../components/DoubleTickTabs';

const emptyArea = {
    name: '',
    city: '',
    state: '',
    distribution_mode: 'broadcast_claim',
    priority: 0,
    claim_timeout_minutes: 30,
    contact_start_timeout_minutes: 10,
    auto_release_enabled: false,
    is_active: true,
    description: '',
};

const emptyAlias = {
    lead_area: '',
    alias: '',
    is_active: true,
    created_from_manual_mapping: true,
};

const SelectField = ({ label, value, onChange, children }) => (
    <label>
        <span className="block text-sm font-medium text-text-secondary mb-1">{label}</span>
        <select
            value={value}
            onChange={(event) => onChange(event.target.value)}
            className="block w-full px-3 py-2 rounded-lg border border-border bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-sm transition"
        >
            {children}
        </select>
    </label>
);

const CheckField = ({ label, checked, onChange }) => (
    <label className="inline-flex items-center gap-2 text-sm text-text-secondary">
        <input
            type="checkbox"
            checked={checked}
            onChange={(event) => onChange(event.target.checked)}
            className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
        />
        {label}
    </label>
);

const SectionHeader = ({ icon, title, subtitle }) => (
    <div className="flex items-start gap-3">
        <div className="bg-background border border-border rounded-lg p-2">
            {React.createElement(icon, { size: 18, className: 'text-primary' })}
        </div>
        <div>
            <h2 className="font-semibold text-text-primary">{title}</h2>
            <p className="text-sm text-text-secondary">{subtitle}</p>
        </div>
    </div>
);

const DoubleTickAreas = () => {
    const [areas, setAreas] = useState([]);
    const [aliases, setAliases] = useState([]);
    const [areaForm, setAreaForm] = useState(emptyArea);
    const [aliasForm, setAliasForm] = useState(emptyAlias);
    const [editingAreaId, setEditingAreaId] = useState(null);
    const [editingAliasId, setEditingAliasId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState('');

    const activeAreas = useMemo(() => areas.filter((area) => area.is_active), [areas]);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [areaRes, aliasRes] = await Promise.all([
                doubletickAPI.getAreas({ all: true }),
                doubletickAPI.getAreaAliases({ all: true }),
            ]);
            setAreas(getList(areaRes));
            setAliases(getList(aliasRes));
        } catch (error) {
            console.error('Failed to load DoubleTick area setup data', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const saveArea = async (event) => {
        event.preventDefault();
        setSaving('area');
        try {
            const payload = {
                ...areaForm,
                priority: Number(areaForm.priority || 0),
                claim_timeout_minutes: Number(areaForm.claim_timeout_minutes || 30),
                contact_start_timeout_minutes: Number(areaForm.contact_start_timeout_minutes || 10),
            };
            if (editingAreaId) {
                await doubletickAPI.updateArea(editingAreaId, payload);
            } else {
                await doubletickAPI.createArea(payload);
            }
            setAreaForm(emptyArea);
            setEditingAreaId(null);
            await loadData();
        } catch (error) {
            alert(error?.response?.data?.detail || 'Unable to save area.');
        } finally {
            setSaving('');
        }
    };

    const saveAlias = async (event) => {
        event.preventDefault();
        setSaving('alias');
        try {
            if (editingAliasId) {
                await doubletickAPI.updateAreaAlias(editingAliasId, aliasForm);
            } else {
                await doubletickAPI.createAreaAlias(aliasForm);
            }
            setAliasForm(emptyAlias);
            setEditingAliasId(null);
            await loadData();
        } catch (error) {
            alert(error?.response?.data?.detail || 'Unable to save alias.');
        } finally {
            setSaving('');
        }
    };

    const editArea = (area) => {
        setEditingAreaId(area.id);
        setAreaForm({
            name: area.name || '',
            city: area.city || '',
            state: area.state || '',
            distribution_mode: area.distribution_mode || 'broadcast_claim',
            priority: area.priority || 0,
            claim_timeout_minutes: area.claim_timeout_minutes || 30,
            contact_start_timeout_minutes: area.contact_start_timeout_minutes || 10,
            auto_release_enabled: Boolean(area.auto_release_enabled),
            is_active: Boolean(area.is_active),
            description: area.description || '',
        });
    };

    const editAlias = (alias) => {
        setEditingAliasId(alias.id);
        setAliasForm({
            lead_area: alias.lead_area || '',
            alias: alias.alias || '',
            is_active: Boolean(alias.is_active),
            created_from_manual_mapping: Boolean(alias.created_from_manual_mapping),
        });
    };

    const removeArea = async (area) => {
        if (!window.confirm('Delete this lead area?')) return;
        await doubletickAPI.deleteArea(area.id);
        await loadData();
    };

    const removeAlias = async (alias) => {
        if (!window.confirm('Delete this area alias?')) return;
        await doubletickAPI.deleteAreaAlias(alias.id);
        await loadData();
    };

    const areaColumns = [
        { header: 'Lead Area', render: (row) => <div><p className="font-medium">{row.name}</p><p className="text-xs text-text-secondary">{row.city || '-'} {row.state || ''}</p></div> },
        { header: 'Distribution', accessor: 'distribution_mode' },
        { header: 'Priority', accessor: 'priority' },
        { header: 'Aliases', accessor: 'alias_count' },
        { header: 'Mapped Branches', accessor: 'branch_mapping_count' },
        { header: 'Status', render: (row) => <Badge variant={row.is_active ? 'success' : 'gray'}>{row.is_active ? 'Active' : 'Inactive'}</Badge> },
        { header: 'Actions', render: (row) => <div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => editArea(row)}>Edit</Button><Button size="sm" variant="ghost" onClick={() => removeArea(row)}><Trash2 size={14} /></Button></div> },
    ];

    const aliasColumns = [
        { header: 'Alias', render: (row) => <div><p className="font-medium">{row.alias}</p><p className="text-xs text-text-secondary">{row.normalized_alias}</p></div> },
        { header: 'Lead Area', accessor: 'lead_area_name' },
        { header: 'Status', render: (row) => <Badge variant={row.is_active ? 'success' : 'gray'}>{row.is_active ? 'Active' : 'Inactive'}</Badge> },
        { header: 'Actions', render: (row) => <div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => editAlias(row)}>Edit</Button><Button size="sm" variant="ghost" onClick={() => removeAlias(row)}><Trash2 size={14} /></Button></div> },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Area Setup</h1>
                    <p className="text-sm text-text-secondary">Create the controlled lead areas and aliases used for automatic DoubleTick matching.</p>
                </div>
                <Button variant="secondary" className="gap-2" onClick={loadData} loading={loading}>
                    <RefreshCw size={16} /> Refresh
                </Button>
            </div>
            <DoubleTickTabs />

            <div className="grid grid-cols-1 xl:grid-cols-[1.2fr_0.8fr] gap-4">
                <form onSubmit={saveArea} className="bg-card border border-border rounded-lg p-5 space-y-4">
                    <SectionHeader icon={MapPin} title={editingAreaId ? 'Edit Lead Area' : 'Create Lead Area'} subtitle="These are the official CRM areas used for lead assignment." />
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <Input label="Area name" value={areaForm.name} onChange={(e) => setAreaForm((prev) => ({ ...prev, name: e.target.value }))} required />
                        <Input label="City" value={areaForm.city} onChange={(e) => setAreaForm((prev) => ({ ...prev, city: e.target.value }))} />
                        <Input label="State" value={areaForm.state} onChange={(e) => setAreaForm((prev) => ({ ...prev, state: e.target.value }))} />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <SelectField label="Distribution" value={areaForm.distribution_mode} onChange={(value) => setAreaForm((prev) => ({ ...prev, distribution_mode: value }))}>
                            <option value="broadcast_claim">Broadcast claim</option>
                            <option value="round_robin">Round robin</option>
                            <option value="manual">Manual</option>
                        </SelectField>
                        <Input label="Priority" type="number" value={areaForm.priority} onChange={(e) => setAreaForm((prev) => ({ ...prev, priority: e.target.value }))} />
                        <Input label="Claim timeout" type="number" value={areaForm.claim_timeout_minutes} onChange={(e) => setAreaForm((prev) => ({ ...prev, claim_timeout_minutes: e.target.value }))} />
                        <Input label="Contact timeout" type="number" value={areaForm.contact_start_timeout_minutes} onChange={(e) => setAreaForm((prev) => ({ ...prev, contact_start_timeout_minutes: e.target.value }))} />
                    </div>
                    <Input label="Description" value={areaForm.description} onChange={(e) => setAreaForm((prev) => ({ ...prev, description: e.target.value }))} />
                    <div className="flex flex-wrap gap-4">
                        <CheckField label="Active" checked={areaForm.is_active} onChange={(value) => setAreaForm((prev) => ({ ...prev, is_active: value }))} />
                        <CheckField label="Auto release" checked={areaForm.auto_release_enabled} onChange={(value) => setAreaForm((prev) => ({ ...prev, auto_release_enabled: value }))} />
                    </div>
                    <div className="flex gap-2">
                        <Button type="submit" className="gap-2" loading={saving === 'area'}><Save size={16} /> Save Area</Button>
                        {editingAreaId && <Button type="button" variant="secondary" onClick={() => { setEditingAreaId(null); setAreaForm(emptyArea); }}>Cancel</Button>}
                    </div>
                </form>

                <form onSubmit={saveAlias} className="bg-card border border-border rounded-lg p-5 space-y-4">
                    <SectionHeader icon={Settings2} title={editingAliasId ? 'Edit Alias' : 'Add Area Alias'} subtitle="Alias text from customers, ads, or bot replies." />
                    <SelectField label="Lead area" value={aliasForm.lead_area} onChange={(value) => setAliasForm((prev) => ({ ...prev, lead_area: value }))}>
                        <option value="">Select area</option>
                        {activeAreas.map((area) => <option key={area.id} value={area.id}>{area.name} {area.city ? `- ${area.city}` : ''}</option>)}
                    </SelectField>
                    <Input label="Alias" value={aliasForm.alias} onChange={(e) => setAliasForm((prev) => ({ ...prev, alias: e.target.value }))} required />
                    <CheckField label="Alias active" checked={aliasForm.is_active} onChange={(value) => setAliasForm((prev) => ({ ...prev, is_active: value }))} />
                    <div className="flex gap-2">
                        <Button type="submit" className="gap-2" loading={saving === 'alias'} disabled={!aliasForm.lead_area}>
                            <Plus size={16} /> Save Alias
                        </Button>
                        {editingAliasId && <Button type="button" variant="secondary" onClick={() => { setEditingAliasId(null); setAliasForm(emptyAlias); }}>Cancel</Button>}
                    </div>
                </form>
            </div>

            <div className="bg-card border border-border rounded-lg p-5 space-y-3">
                <SectionHeader icon={MapPin} title="Lead Areas" subtitle="Area records drive automatic matching and assignment rules." />
                <Table columns={areaColumns} data={areas} onRowClick={editArea} />
            </div>

            <div className="bg-card border border-border rounded-lg p-5 space-y-3">
                <SectionHeader icon={Settings2} title="Area Aliases" subtitle="Aliases increase successful area matching from customer messages." />
                <Table columns={aliasColumns} data={aliases} onRowClick={editAlias} />
            </div>
        </div>
    );
};

export default DoubleTickAreas;
