import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, CheckSquare, GitBranch, ListTree, PanelRight, RefreshCw, Save, Search, Trash2, X } from 'lucide-react';
import Badge from '../../../shared/components/Badge';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';
import Table from '../../../shared/components/Table';
import { branchesAPI } from '../../branches/api';
import { doubletickAPI } from '../api';
import { getList } from '../utils';
import DoubleTickTabs from '../components/DoubleTickTabs';

const emptyMapping = {
    lead_area: '',
    branches: [],
    priority: 0,
    is_active: true,
    receives_leads: true,
    notes: '',
};

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

const BranchMultiSelect = ({ branches, value, onChange, disabled }) => {
    const [search, setSearch] = useState('');
    const selectedSet = useMemo(() => new Set(value), [value]);
    const selectedBranches = useMemo(() => branches.filter((branch) => selectedSet.has(branch.id)), [branches, selectedSet]);
    const filteredBranches = useMemo(() => {
        const term = search.trim().toLowerCase();
        if (!term) return branches;
        return branches.filter((branch) => (
            `${branch.spa_name || ''} ${branch.area || ''} ${branch.city || ''} ${branch.state || ''} ${branch.code || ''}`.toLowerCase().includes(term)
        ));
    }, [branches, search]);

    const toggleBranch = (branchId) => {
        if (disabled) return;
        if (selectedSet.has(branchId)) {
            onChange(value.filter((id) => id !== branchId));
            return;
        }
        onChange([...value, branchId]);
    };

    const selectFiltered = () => {
        const next = new Set(value);
        filteredBranches.forEach((branch) => next.add(branch.id));
        onChange([...next]);
    };

    return (
        <div className="space-y-3">
            <div>
                <div className="flex items-center justify-between mb-1">
                    <span className="block text-sm font-medium text-text-secondary">Spa branches</span>
                    <span className="text-xs text-text-secondary">{value.length} selected</span>
                </div>
                <div className="relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                    <input
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Search branch, city, area, spa code"
                        disabled={disabled}
                        className="block w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-sm transition"
                    />
                </div>
            </div>
            <div className="flex flex-wrap gap-2">
                <Button type="button" size="sm" variant="secondary" className="gap-2" onClick={selectFiltered} disabled={disabled || filteredBranches.length === 0}>
                    <CheckSquare size={14} /> Select shown
                </Button>
                <Button type="button" size="sm" variant="ghost" className="gap-2" onClick={() => onChange([])} disabled={disabled || value.length === 0}>
                    <X size={14} /> Clear
                </Button>
            </div>
            {selectedBranches.length > 0 && (
                <div className="flex flex-wrap gap-2">
                    {selectedBranches.map((branch) => (
                        <button
                            key={branch.id}
                            type="button"
                            onClick={() => toggleBranch(branch.id)}
                            className="inline-flex items-center gap-1 rounded-md bg-primary/10 text-primary border border-primary/20 px-2 py-1 text-xs"
                        >
                            {branch.spa_name}
                            <X size={12} />
                        </button>
                    ))}
                </div>
            )}
            <div className="border border-border rounded-lg overflow-hidden max-h-[300px] overflow-y-auto bg-background">
                {filteredBranches.length === 0 ? (
                    <div className="p-4 text-sm text-text-secondary text-center">No branches found</div>
                ) : (
                    filteredBranches.map((branch) => (
                        <label key={branch.id} className="flex items-start gap-3 px-3 py-2 border-b border-border last:border-b-0 hover:bg-card cursor-pointer">
                            <input
                                type="checkbox"
                                checked={selectedSet.has(branch.id)}
                                onChange={() => toggleBranch(branch.id)}
                                disabled={disabled}
                                className="mt-1 h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                            />
                            <span>
                                <span className="block text-sm font-medium text-text-primary">{branch.spa_name}</span>
                                <span className="block text-xs text-text-secondary">{branch.area || '-'} - {branch.city || '-'} {branch.state || ''} {branch.code ? `- ${branch.code}` : ''}</span>
                            </span>
                        </label>
                    ))
                )}
            </div>
        </div>
    );
};

const WorkspaceTabs = ({ value, onChange }) => (
    <div className="bg-card border border-border rounded-lg p-1 flex flex-wrap gap-1">
        {[
            { id: 'area-map', label: 'Lead Area Map', icon: GitBranch },
            { id: 'mapped-branches', label: 'Lead Mapped Branch', icon: ListTree },
        ].map((tab) => (
            <button
                key={tab.id}
                type="button"
                onClick={() => onChange(tab.id)}
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition ${
                    value === tab.id ? 'bg-primary text-white' : 'text-text-secondary hover:bg-background hover:text-text-primary'
                }`}
            >
                <tab.icon size={16} />
                {tab.label}
            </button>
        ))}
    </div>
);

const DoubleTickAreaMap = () => {
    const [areas, setAreas] = useState([]);
    const [branches, setBranches] = useState([]);
    const [mappings, setMappings] = useState([]);
    const [mappingForm, setMappingForm] = useState(emptyMapping);
    const [selectedAreaId, setSelectedAreaId] = useState('');
    const [selectedMappingId, setSelectedMappingId] = useState('');
    const [editingMappingId, setEditingMappingId] = useState(null);
    const [workspaceTab, setWorkspaceTab] = useState('area-map');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [bulkDeleting, setBulkDeleting] = useState(false);
    const [selectedAreaMappingIds, setSelectedAreaMappingIds] = useState([]);
    const [selectedMappedBranchIds, setSelectedMappedBranchIds] = useState([]);

    const activeAreas = useMemo(() => areas.filter((area) => area.is_active), [areas]);
    const activeBranches = useMemo(() => branches.filter((branch) => branch.is_active), [branches]);
    const mappedBranchCount = useMemo(() => new Set(mappings.filter((item) => item.is_active && item.receives_leads).map((item) => item.branch)).size, [mappings]);
    const mappedAreaIds = useMemo(() => new Set(mappings.map((item) => item.lead_area)), [mappings]);
    const mappedAreas = useMemo(() => activeAreas.filter((area) => mappedAreaIds.has(area.id)), [activeAreas, mappedAreaIds]);
    const unmappedAreas = useMemo(() => activeAreas.filter((area) => !mappedAreaIds.has(area.id)), [activeAreas, mappedAreaIds]);
    const selectedArea = useMemo(() => activeAreas.find((area) => area.id === selectedAreaId), [activeAreas, selectedAreaId]);
    const selectedAreaMappings = useMemo(() => mappings.filter((item) => item.lead_area === selectedAreaId), [mappings, selectedAreaId]);
    const selectedMapping = useMemo(() => mappings.find((item) => item.id === selectedMappingId) || null, [mappings, selectedMappingId]);
    const selectedAreaBranchIds = useMemo(() => new Set(selectedAreaMappings.map((item) => item.branch)), [selectedAreaMappings]);
    const availableBranches = useMemo(() => {
        if (!selectedAreaId || editingMappingId) return activeBranches;
        return activeBranches.filter((branch) => !selectedAreaBranchIds.has(branch.id));
    }, [activeBranches, editingMappingId, selectedAreaBranchIds, selectedAreaId]);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [areaRes, branchRes, mappingRes] = await Promise.all([
                doubletickAPI.getAreas({ all: true, is_active: true }),
                branchesAPI.getBranches({ all: true }),
                doubletickAPI.getAreaBranches({ all: true }),
            ]);
            setAreas(getList(areaRes));
            setBranches(getList(branchRes));
            setMappings(getList(mappingRes));
            setSelectedAreaMappingIds((prev) => prev.filter((id) => getList(mappingRes).some((item) => item.id === id)));
            setSelectedMappedBranchIds((prev) => prev.filter((id) => getList(mappingRes).some((item) => item.id === id)));
        } catch (error) {
            console.error('Failed to load DoubleTick lead area map data', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    useEffect(() => {
        if (selectedAreaId && activeAreas.some((area) => area.id === selectedAreaId)) return;
        const firstArea = mappedAreas[0] || activeAreas[0];
        if (!firstArea) return;
        setSelectedAreaId(firstArea.id);
        setMappingForm((prev) => ({ ...prev, lead_area: firstArea.id, branches: [] }));
    }, [activeAreas, mappedAreas, selectedAreaId]);

    const selectArea = (area) => {
        setSelectedAreaId(area.id);
        setSelectedMappingId('');
        setSelectedAreaMappingIds([]);
        setEditingMappingId(null);
        setWorkspaceTab('area-map');
        setMappingForm({ ...emptyMapping, lead_area: area.id });
    };

    const selectMapping = (mapping) => {
        setWorkspaceTab('mapped-branches');
        setSelectedMappingId(mapping.id);
        setSelectedAreaId(mapping.lead_area || selectedAreaId);
    };

    const saveMapping = async (event) => {
        event.preventDefault();
        setSaving(true);
        try {
            const leadAreaId = mappingForm.lead_area || selectedAreaId;
            const payload = {
                priority: Number(mappingForm.priority || 0),
                is_active: mappingForm.is_active,
                receives_leads: mappingForm.receives_leads,
                notes: mappingForm.notes,
            };

            if (editingMappingId) {
                await doubletickAPI.updateAreaBranch(editingMappingId, {
                    ...payload,
                    lead_area: leadAreaId,
                    branch: mappingForm.branches[0],
                });
            } else {
                const existingByBranch = new Map(
                    mappings
                        .filter((item) => item.lead_area === leadAreaId)
                        .map((item) => [item.branch, item])
                );
                await Promise.all(mappingForm.branches.map((branchId) => {
                    const existing = existingByBranch.get(branchId);
                    const rowPayload = { ...payload, lead_area: leadAreaId, branch: branchId };
                    return existing
                        ? doubletickAPI.updateAreaBranch(existing.id, rowPayload)
                        : doubletickAPI.createAreaBranch(rowPayload);
                }));
            }

            setMappingForm({ ...emptyMapping, lead_area: selectedAreaId });
            setEditingMappingId(null);
            await loadData();
        } catch (error) {
            const data = error?.response?.data;
            alert(data?.non_field_errors?.[0] || data?.detail || 'Unable to save lead area mapping.');
        } finally {
            setSaving(false);
        }
    };

    const editMapping = (mapping) => {
        setEditingMappingId(mapping.id);
        setSelectedMappingId(mapping.id);
        setSelectedAreaId(mapping.lead_area || '');
        setMappingForm({
            lead_area: mapping.lead_area || '',
            branches: mapping.branch ? [mapping.branch] : [],
            priority: mapping.priority || 0,
            is_active: Boolean(mapping.is_active),
            receives_leads: Boolean(mapping.receives_leads),
            notes: mapping.notes || '',
        });
        setWorkspaceTab('area-map');
    };

    const removeMapping = async (mapping) => {
        if (!window.confirm('Delete this lead area branch mapping?')) return;
        await doubletickAPI.deleteAreaBranch(mapping.id);
        if (selectedMappingId === mapping.id) {
            setSelectedMappingId('');
        }
        setSelectedAreaMappingIds((prev) => prev.filter((id) => id !== mapping.id));
        setSelectedMappedBranchIds((prev) => prev.filter((id) => id !== mapping.id));
        await loadData();
    };

    const bulkDeleteMappings = async (ids, label = 'selected mappings') => {
        const uniqueIds = [...new Set(ids)].filter(Boolean);
        if (uniqueIds.length === 0) return;
        if (!window.confirm(`Delete ${uniqueIds.length} ${label}? This cannot be undone.`)) return;

        setBulkDeleting(true);
        try {
            await Promise.all(uniqueIds.map((id) => doubletickAPI.deleteAreaBranch(id)));
            if (uniqueIds.includes(selectedMappingId)) {
                setSelectedMappingId('');
            }
            setSelectedAreaMappingIds((prev) => prev.filter((id) => !uniqueIds.includes(id)));
            setSelectedMappedBranchIds((prev) => prev.filter((id) => !uniqueIds.includes(id)));
            await loadData();
        } catch (error) {
            const data = error?.response?.data;
            alert(data?.detail || 'Unable to delete selected mappings.');
        } finally {
            setBulkDeleting(false);
        }
    };

    const areaColumns = [
        { header: 'Lead Area', render: (row) => <div><p className="font-medium">{row.name}</p><p className="text-xs text-text-secondary">{row.city || '-'} {row.state || ''}</p></div> },
        { header: 'Mapped Spas', render: (row) => mappings.filter((item) => item.lead_area === row.id && item.is_active && item.receives_leads).length },
        { header: 'Status', render: (row) => <Badge variant={row.id === selectedAreaId ? 'info' : 'success'}>{row.id === selectedAreaId ? 'Open' : 'Mapped'}</Badge> },
    ];

    const unmappedAreaColumns = [
        { header: 'Lead Area', render: (row) => <div><p className="font-medium">{row.name}</p><p className="text-xs text-text-secondary">{row.city || '-'} {row.state || ''}</p></div> },
        { header: 'Status', render: () => <Badge variant="warning">No branches</Badge> },
        { header: 'Action', render: (row) => <Button size="sm" variant="secondary" onClick={() => selectArea(row)}>Map</Button> },
    ];

    const mappingColumns = [
        { header: 'Spa Branch', render: (row) => <div><p className="font-medium">{row.branch_name}</p><p className="text-xs text-text-secondary">{row.branch_area || '-'} - {row.branch_city || '-'} {row.branch_state || ''}</p></div> },
        { header: 'Priority', accessor: 'priority' },
        { header: 'Receives Leads', render: (row) => <Badge variant={row.is_active && row.receives_leads ? 'success' : 'gray'}>{row.is_active && row.receives_leads ? 'Enabled' : 'Disabled'}</Badge> },
        { header: 'Notes', render: (row) => row.notes || '-' },
        { header: 'Actions', render: (row) => <div className="flex gap-2"><Button size="sm" variant="secondary" onClick={() => editMapping(row)}>Edit</Button><Button size="sm" variant="ghost" onClick={() => removeMapping(row)}><Trash2 size={14} /></Button></div> },
    ];

    const mappedBranchColumns = [
        { header: 'Lead Area', render: (row) => <div><p className="font-medium">{row.lead_area_name}</p><p className="text-xs text-text-secondary">Priority {row.priority}</p></div> },
        { header: 'Spa Branch', render: (row) => <div><p className="font-medium">{row.branch_name}</p><p className="text-xs text-text-secondary">{row.branch_area || '-'} - {row.branch_city || '-'} {row.branch_state || ''}</p></div> },
        { header: 'Receives Leads', render: (row) => <Badge variant={row.is_active && row.receives_leads ? 'success' : 'gray'}>{row.is_active && row.receives_leads ? 'Enabled' : 'Disabled'}</Badge> },
        { header: 'Notes', render: (row) => row.notes || '-' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Lead Area Map</h1>
                    <p className="text-sm text-text-secondary">Map created DoubleTick areas to the spa branches whose managers should receive those leads.</p>
                </div>
                <Button variant="secondary" className="gap-2" onClick={loadData} loading={loading}>
                    <RefreshCw size={16} /> Refresh
                </Button>
            </div>
            <DoubleTickTabs />
            <WorkspaceTabs value={workspaceTab} onChange={setWorkspaceTab} />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs uppercase text-text-secondary font-semibold">Created Areas</p>
                    <p className="text-2xl font-bold text-text-primary">{activeAreas.length}</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs uppercase text-text-secondary font-semibold">Mapped Areas</p>
                    <p className="text-2xl font-bold text-text-primary">{mappedAreas.length}</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs uppercase text-text-secondary font-semibold">Mapped Branches</p>
                    <p className="text-2xl font-bold text-text-primary">{mappedBranchCount}</p>
                </div>
            </div>

            {workspaceTab === 'area-map' && (
                <>
                    <div className="grid grid-cols-1 xl:grid-cols-[0.9fr_1.1fr] gap-4">
                        <div className="space-y-4">
                            <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                                <SectionHeader icon={GitBranch} title="Created Area Mappings" subtitle="Open an area to manage only its mapped spa branches." />
                                <Table columns={areaColumns} data={mappedAreas} onRowClick={selectArea} />
                            </div>
                            <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                                <SectionHeader icon={Building2} title="Areas Waiting For Branches" subtitle="Created lead areas that do not have spa branches mapped yet." />
                                <Table columns={unmappedAreaColumns} data={unmappedAreas} onRowClick={selectArea} />
                            </div>
                        </div>

                        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                            <SectionHeader
                                icon={PanelRight}
                                title={selectedArea ? `${selectedArea.name} Branch Detail` : 'Branch Detail'}
                                subtitle={selectedArea ? `${selectedAreaMappings.length} spa branch mapping${selectedAreaMappings.length === 1 ? '' : 's'} for this area.` : 'Select an area to view branch mappings.'}
                            />
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <p className="text-sm text-text-secondary">
                                    {selectedAreaMappingIds.length} selected in this area
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    <Button
                                        size="sm"
                                        variant="secondary"
                                        onClick={() => setSelectedAreaMappingIds(selectedAreaMappings.map((item) => item.id))}
                                        disabled={selectedAreaMappings.length === 0}
                                    >
                                        Select All
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setSelectedAreaMappingIds([])}
                                        disabled={selectedAreaMappingIds.length === 0}
                                    >
                                        Clear
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="danger"
                                        className="gap-2"
                                        loading={bulkDeleting}
                                        onClick={() => bulkDeleteMappings(selectedAreaMappingIds, 'area branch mappings')}
                                        disabled={selectedAreaMappingIds.length === 0}
                                    >
                                        <Trash2 size={14} /> Delete Selected
                                    </Button>
                                    <Button
                                        size="sm"
                                        variant="danger"
                                        className="gap-2"
                                        loading={bulkDeleting}
                                        onClick={() => bulkDeleteMappings(selectedAreaMappings.map((item) => item.id), 'area branch mappings')}
                                        disabled={selectedAreaMappings.length === 0}
                                    >
                                        <Trash2 size={14} /> Delete All
                                    </Button>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">Area</p>
                                    <p className="text-text-secondary mt-1">{selectedArea?.name || '-'}</p>
                                </div>
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">Location</p>
                                    <p className="text-text-secondary mt-1">{selectedArea ? `${selectedArea.city || '-'} ${selectedArea.state || ''}` : '-'}</p>
                                </div>
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">Receiving Spas</p>
                                    <p className="text-text-secondary mt-1">{selectedAreaMappings.filter((item) => item.is_active && item.receives_leads).length}</p>
                                </div>
                            </div>
                            <Table
                                columns={mappingColumns}
                                data={selectedAreaMappings}
                                onRowClick={selectMapping}
                                selectable
                                selectedIds={selectedAreaMappingIds}
                                onSelectionChange={(ids) => setSelectedAreaMappingIds(ids)}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 xl:grid-cols-[0.8fr_1.2fr] gap-4">
                        <form onSubmit={saveMapping} className="bg-card border border-border rounded-lg p-5 space-y-4">
                            <SectionHeader
                                icon={GitBranch}
                                title={editingMappingId ? 'Edit Branch Mapping' : `Add Branches${selectedArea ? ` To ${selectedArea.name}` : ''}`}
                                subtitle="Select one area, then choose one or more spa branches for that area."
                            />
                            <div className="bg-background border border-border rounded-lg p-3">
                                <p className="text-xs uppercase text-text-secondary font-semibold">Selected lead area</p>
                                <p className="font-semibold text-text-primary mt-1">{selectedArea?.name || 'Select an area from the mapped area list'}</p>
                                {selectedArea && <p className="text-xs text-text-secondary">{selectedArea.city || '-'} {selectedArea.state || ''}</p>}
                            </div>
                            <BranchMultiSelect
                                branches={availableBranches}
                                value={mappingForm.branches}
                                onChange={(value) => setMappingForm((prev) => ({ ...prev, branches: value }))}
                                disabled={!selectedAreaId || Boolean(editingMappingId)}
                            />
                            <Input label="Priority" type="number" value={mappingForm.priority} onChange={(e) => setMappingForm((prev) => ({ ...prev, priority: e.target.value }))} />
                            <Input label="Notes" value={mappingForm.notes} onChange={(e) => setMappingForm((prev) => ({ ...prev, notes: e.target.value }))} />
                            <div className="flex flex-wrap gap-4">
                                <CheckField label="Mapping active" checked={mappingForm.is_active} onChange={(value) => setMappingForm((prev) => ({ ...prev, is_active: value }))} />
                                <CheckField label="Branch receives leads" checked={mappingForm.receives_leads} onChange={(value) => setMappingForm((prev) => ({ ...prev, receives_leads: value }))} />
                            </div>
                            <div className="flex gap-2">
                                <Button type="submit" className="gap-2" loading={saving} disabled={!selectedAreaId || mappingForm.branches.length === 0}>
                                    <Save size={16} /> {editingMappingId ? 'Save Mapping' : `Save ${mappingForm.branches.length || ''} Mapping${mappingForm.branches.length === 1 ? '' : 's'}`}
                                </Button>
                                {editingMappingId && <Button type="button" variant="secondary" onClick={() => { setEditingMappingId(null); setMappingForm({ ...emptyMapping, lead_area: selectedAreaId }); }}>Cancel</Button>}
                            </div>
                        </form>

                        <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                            <SectionHeader icon={Building2} title="Assignment Behavior" subtitle="After an area is matched, mapped active branches receive the lead." />
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">1. Area matched</p>
                                    <p className="text-text-secondary mt-1">CRM matches customer location to a controlled lead area.</p>
                                </div>
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">2. Branch visibility</p>
                                    <p className="text-text-secondary mt-1">Active mapped branches receive visibility for the lead.</p>
                                </div>
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="font-medium text-text-primary">3. Manager app</p>
                                    <p className="text-text-secondary mt-1">Spa managers assigned to those branches can see and claim the lead.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {workspaceTab === 'mapped-branches' && (
                <div className="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-4">
                    <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                        <SectionHeader icon={ListTree} title="Lead Mapped Branch List" subtitle="Every spa branch currently connected to a DoubleTick lead area." />
                        <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="text-sm text-text-secondary">
                                {selectedMappedBranchIds.length} selected from {mappings.length} mappings
                            </p>
                            <div className="flex flex-wrap gap-2">
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={() => setSelectedMappedBranchIds(mappings.map((item) => item.id))}
                                    disabled={mappings.length === 0}
                                >
                                    Select All
                                </Button>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => setSelectedMappedBranchIds([])}
                                    disabled={selectedMappedBranchIds.length === 0}
                                >
                                    Clear
                                </Button>
                                <Button
                                    size="sm"
                                    variant="danger"
                                    className="gap-2"
                                    loading={bulkDeleting}
                                    onClick={() => bulkDeleteMappings(selectedMappedBranchIds, 'mapped branch rows')}
                                    disabled={selectedMappedBranchIds.length === 0}
                                >
                                    <Trash2 size={14} /> Delete Selected
                                </Button>
                                <Button
                                    size="sm"
                                    variant="danger"
                                    className="gap-2"
                                    loading={bulkDeleting}
                                    onClick={() => bulkDeleteMappings(mappings.map((item) => item.id), 'mapped branch rows')}
                                    disabled={mappings.length === 0}
                                >
                                    <Trash2 size={14} /> Delete All
                                </Button>
                            </div>
                        </div>
                        <Table
                            columns={mappedBranchColumns}
                            data={mappings}
                            onRowClick={selectMapping}
                            selectable
                            selectedIds={selectedMappedBranchIds}
                            onSelectionChange={(ids) => setSelectedMappedBranchIds(ids)}
                        />
                    </div>
                    <div className="bg-card border border-border rounded-lg p-5 space-y-4">
                        <SectionHeader icon={PanelRight} title="Mapped Branch Side Panel" subtitle="Select one mapped branch row to inspect or edit it." />
                        {selectedMapping ? (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                    <div className="bg-background border border-border rounded-lg p-3">
                                        <p className="text-xs uppercase text-text-secondary font-semibold">Lead Area</p>
                                        <p className="font-semibold text-text-primary mt-1">{selectedMapping.lead_area_name}</p>
                                    </div>
                                    <div className="bg-background border border-border rounded-lg p-3">
                                        <p className="text-xs uppercase text-text-secondary font-semibold">Spa Branch</p>
                                        <p className="font-semibold text-text-primary mt-1">{selectedMapping.branch_name}</p>
                                        <p className="text-xs text-text-secondary">{selectedMapping.branch_area || '-'} - {selectedMapping.branch_city || '-'} {selectedMapping.branch_state || ''}</p>
                                    </div>
                                    <div className="bg-background border border-border rounded-lg p-3">
                                        <p className="text-xs uppercase text-text-secondary font-semibold">Priority</p>
                                        <p className="font-semibold text-text-primary mt-1">{selectedMapping.priority}</p>
                                    </div>
                                    <div className="bg-background border border-border rounded-lg p-3">
                                        <p className="text-xs uppercase text-text-secondary font-semibold">Status</p>
                                        <div className="mt-2">
                                            <Badge variant={selectedMapping.is_active && selectedMapping.receives_leads ? 'success' : 'gray'}>
                                                {selectedMapping.is_active && selectedMapping.receives_leads ? 'Receiving leads' : 'Disabled'}
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                                <div className="bg-background border border-border rounded-lg p-3">
                                    <p className="text-xs uppercase text-text-secondary font-semibold">Notes</p>
                                    <p className="text-sm text-text-primary mt-1">{selectedMapping.notes || '-'}</p>
                                </div>
                                <div className="flex gap-2">
                                    <Button variant="secondary" onClick={() => editMapping(selectedMapping)}>Edit Mapping</Button>
                                    <Button variant="ghost" className="gap-2" onClick={() => removeMapping(selectedMapping)}><Trash2 size={14} /> Delete</Button>
                                </div>
                            </>
                        ) : (
                            <div className="bg-background border border-border rounded-lg p-8 text-center text-sm text-text-secondary">
                                Select a mapped branch from the list.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default DoubleTickAreaMap;
