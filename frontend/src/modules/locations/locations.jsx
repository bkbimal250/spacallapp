import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
    AlertTriangle,
    CheckSquare,
    CheckCircle2,
    Eye,
    GitMerge,
    Layers,
    ListPlus,
    Map,
    MapPin,
    Pencil,
    RefreshCcw,
    Route,
    Save,
    Search,
    Square,
    X,
} from 'lucide-react';
import Button from '../../shared/components/Button';
import Input from '../../shared/components/Input';
import SearchableSelect from '../../shared/components/SearchableSelect';
import BulkAddBox from './components/BulkAddBox';
import LocationDataTable from './components/LocationDataTable';
import LocationSection from './components/LocationSection';
import LocationSelectors from './components/LocationSelectors';
import QuickCreateForm from './components/QuickCreateForm';
import { locationsAPI } from './api';
import { formatLocation, getRecordId, toOptions, unpackList } from './utils';

const tabs = [
    { id: 'states', label: 'States', icon: Map },
    { id: 'cities', label: 'Cities', icon: MapPin },
    { id: 'areas', label: 'Areas', icon: Route },
    { id: 'groups', label: 'Groups', icon: Layers },
    { id: 'groupAreas', label: 'Group Areas', icon: GitMerge },
    { id: 'aliases', label: 'Aliases', icon: ListPlus },
    { id: 'matcher', label: 'Matcher', icon: Search },
];

const emptyGroupForm = {
    id: '',
    state: '',
    city: '',
    name: '',
    description: '',
    is_active: true,
    priority: 0,
};

const emptyGroupAreaForm = {
    state: '',
    city: '',
    group: '',
    area_ids: [],
};

const AreaMultiSelect = ({
    areas,
    selectedAreaIds,
    onChange,
    disabled = false,
    loading = false,
    citySelected = false,
    error = '',
}) => {
    const [search, setSearch] = useState('');
    const selectedSet = useMemo(() => new Set(selectedAreaIds), [selectedAreaIds]);
    const filteredAreas = useMemo(() => {
        const query = search.trim().toLowerCase();
        if (!query) return areas;
        return areas.filter((area) => [
            area.name,
            area.normalized_name,
            area.city_name,
            area.state_name,
        ].filter(Boolean).join(' ').toLowerCase().includes(query));
    }, [areas, search]);
    const selectedAreas = useMemo(
        () => areas.filter((area) => selectedSet.has(area.id)),
        [areas, selectedSet]
    );

    const toggleArea = (areaId) => {
        if (disabled) return;
        if (selectedSet.has(areaId)) {
            onChange(selectedAreaIds.filter((id) => id !== areaId));
        } else {
            onChange([...selectedAreaIds, areaId]);
        }
    };

    const selectAll = () => {
        onChange([...new Set([...selectedAreaIds, ...filteredAreas.map((area) => area.id)])]);
    };

    return (
        <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                <div>
                    <p className="text-sm font-semibold text-text-primary">Existing Areas</p>
                    <p className="text-xs text-text-secondary">
                        {selectedAreaIds.length} selected from {areas.length} areas
                    </p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Button type="button" variant="secondary" size="sm" disabled={disabled || !filteredAreas.length} onClick={selectAll}>
                        Select all
                    </Button>
                    <Button type="button" variant="ghost" size="sm" disabled={disabled || !selectedAreaIds.length} onClick={() => onChange([])}>
                        Clear all
                    </Button>
                </div>
            </div>

            <Input
                className="mt-3"
                label="Search areas"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search Panvel, Belapur..."
                disabled={disabled || !citySelected}
            />

            {!citySelected && (
                <p className="mt-3 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-sm text-warning">
                    Select a city before choosing areas.
                </p>
            )}

            {error && (
                <p className="mt-3 rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                    {error}
                </p>
            )}

            {selectedAreas.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                    {selectedAreas.map((area) => (
                        <button
                            type="button"
                            key={area.id}
                            disabled={disabled}
                            onClick={() => toggleArea(area.id)}
                            className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary disabled:opacity-60"
                        >
                            {area.name}
                            <X size={12} />
                        </button>
                    ))}
                </div>
            )}

            <div className="mt-3 max-h-72 overflow-y-auto rounded-lg border border-border bg-background">
                {loading ? (
                    <div className="px-4 py-8 text-center text-sm text-text-secondary">Loading areas...</div>
                ) : !citySelected ? (
                    <div className="px-4 py-8 text-center text-sm text-text-secondary">Choose a city to load areas.</div>
                ) : areas.length === 0 ? (
                    <div className="px-4 py-8 text-center text-sm text-text-secondary">No areas found for this city</div>
                ) : filteredAreas.length === 0 ? (
                    <div className="px-4 py-8 text-center text-sm text-text-secondary">No areas match your search.</div>
                ) : (
                    filteredAreas.map((area) => {
                        const checked = selectedSet.has(area.id);
                        return (
                            <button
                                type="button"
                                key={area.id}
                                disabled={disabled}
                                onClick={() => toggleArea(area.id)}
                                className={`flex w-full items-center justify-between gap-3 border-b border-border px-4 py-2.5 text-left text-sm last:border-b-0 hover:bg-card ${checked ? 'bg-primary/5 text-text-primary' : 'text-text-secondary'}`}
                            >
                                <span>
                                    <span className="font-medium text-text-primary">{area.name}</span>
                                    <span className="ml-2 text-xs text-text-muted">{formatLocation(area.city_name || area.city_detail?.name, area.state_name || area.city_detail?.state_name)}</span>
                                </span>
                                {checked ? <CheckSquare size={17} className="text-primary" /> : <Square size={17} />}
                            </button>
                        );
                    })
                )}
            </div>
        </div>
    );
};

const Locations = () => {
    const [activeTab, setActiveTab] = useState('states');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [states, setStates] = useState([]);
    const [cities, setCities] = useState([]);
    const [areas, setAreas] = useState([]);
    const [groups, setGroups] = useState([]);
    const [cityAliases, setCityAliases] = useState([]);
    const [areaAliases, setAreaAliases] = useState([]);
    const [groupAreas, setGroupAreas] = useState([]);
    const [notice, setNotice] = useState(null);
    const [areaSearch, setAreaSearch] = useState('');
    const [matchText, setMatchText] = useState('');
    const [matchResult, setMatchResult] = useState(null);
    const [groupForm, setGroupForm] = useState(emptyGroupForm);
    const [groupAreaForm, setGroupAreaForm] = useState(emptyGroupAreaForm);
    const [groupFormError, setGroupFormError] = useState('');
    const [groupAreaError, setGroupAreaError] = useState('');
    const [viewingGroupId, setViewingGroupId] = useState('');
    const [selected, setSelected] = useState({
        state: '',
        city: '',
        group: '',
        area: '',
    });

    const selectedStateCities = useMemo(
        () => cities.filter((city) => !selected.state || city.state === selected.state),
        [cities, selected.state]
    );
    const selectedCityAreas = useMemo(
        () => areas.filter((area) => !selected.city || area.city === selected.city),
        [areas, selected.city]
    );
    const selectedCityGroups = useMemo(
        () => groups.filter((group) => !selected.city || group.city === selected.city),
        [groups, selected.city]
    );
    const visibleAreas = useMemo(() => {
        const source = selected.city ? selectedCityAreas : areas;
        const query = areaSearch.trim().toLowerCase();
        if (!query) return source;
        return source.filter((area) => [
            area.name,
            area.normalized_name,
            area.city_name,
            area.city_detail?.name,
            area.state_name,
            area.city_detail?.state_name,
        ].filter(Boolean).join(' ').toLowerCase().includes(query));
    }, [areaSearch, areas, selected.city, selectedCityAreas]);
    const selectedCityName = useMemo(() => {
        return cities.find((city) => city.id === selected.city)?.name || '';
    }, [cities, selected.city]);
    const groupFormCities = useMemo(
        () => cities.filter((city) => !groupForm.state || city.state === groupForm.state),
        [cities, groupForm.state]
    );
    const groupAreaCities = useMemo(
        () => cities.filter((city) => !groupAreaForm.state || city.state === groupAreaForm.state),
        [cities, groupAreaForm.state]
    );
    const groupAreaGroups = useMemo(
        () => groups.filter((group) => groupAreaForm.city && group.city === groupAreaForm.city),
        [groups, groupAreaForm.city]
    );
    const groupAreaAreas = useMemo(
        () => areas.filter((area) => groupAreaForm.city && area.city === groupAreaForm.city),
        [areas, groupAreaForm.city]
    );
    const viewingGroup = useMemo(
        () => groups.find((group) => group.id === viewingGroupId) || null,
        [groups, viewingGroupId]
    );

    const getGroupMappings = useCallback(
        (groupId) => groupAreas.filter((item) => item.group === groupId),
        [groupAreas]
    );

    const getGroupAreaIds = useCallback(
        (groupId) => getGroupMappings(groupId).map((item) => item.area).filter(Boolean),
        [getGroupMappings]
    );

    const getGroupAreasForDisplay = useCallback(
        (groupId) => getGroupMappings(groupId).map((item) => ({
            id: item.area,
            name: item.area_name,
            city_name: item.city_name,
        })),
        [getGroupMappings]
    );

    const loadAliases = useCallback(async () => {
        const [cityAliasesResponse, areaAliasesResponse] = await Promise.all([
            locationsAPI.getCityAliases({ all: true }),
            locationsAPI.getAreaAliases({ all: true }),
        ]);
        setCityAliases(unpackList(cityAliasesResponse));
        setAreaAliases(unpackList(areaAliasesResponse));
    }, []);

    const refresh = useCallback(async () => {
        setLoading(true);
        try {
            const [
                statesResponse,
                citiesResponse,
                areasResponse,
                groupsResponse,
                groupAreasResponse,
            ] = await Promise.all([
                locationsAPI.getStates({ all: true }),
                locationsAPI.getCities({ all: true }),
                locationsAPI.getAreas({ all: true }),
                locationsAPI.getGroups({ all: true }),
                locationsAPI.getGroupAreas({ all: true }),
            ]);
            setStates(unpackList(statesResponse));
            setCities(unpackList(citiesResponse));
            setAreas(unpackList(areasResponse));
            setGroups(unpackList(groupsResponse));
            setGroupAreas(unpackList(groupAreasResponse));
        } catch (error) {
            console.error('Failed to load locations', error);
            window.alert('Failed to load locations.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    useEffect(() => {
        if (activeTab !== 'aliases') return;

        setLoading(true);
        loadAliases()
            .catch((error) => {
                console.error('Failed to load location aliases', error);
                window.alert('Failed to load aliases.');
            })
            .finally(() => setLoading(false));
    }, [activeTab, loadAliases]);

    const updateSelected = (key, value) => {
        setSelected((prev) => {
            const next = { ...prev, [key]: value };
            if (key === 'state') {
                next.city = '';
                next.group = '';
                next.area = '';
            }
            if (key === 'city') {
                next.group = '';
                next.area = '';
            }
            if (key === 'group') {
                next.area = '';
            }
            return next;
        });
    };

    const updateGroupForm = (key, value) => {
        setGroupForm((prev) => {
            const next = { ...prev, [key]: value };
            if (key === 'state') {
                next.city = '';
            }
            return next;
        });
        setGroupFormError('');
    };

    const updateGroupAreaForm = (key, value) => {
        setGroupAreaForm((prev) => {
            const next = { ...prev, [key]: value };
            if (key === 'state') {
                next.city = '';
                next.group = '';
                next.area_ids = [];
            }
            if (key === 'city') {
                next.group = '';
                next.area_ids = [];
            }
            if (key === 'group') {
                next.area_ids = value ? getGroupAreaIds(value) : [];
            }
            return next;
        });
        setGroupAreaError('');
    };

    const startCreateGroup = () => {
        setGroupForm({
            ...emptyGroupForm,
            state: selected.state,
            city: selected.city,
        });
        setGroupFormError('');
    };

    const startEditGroup = (group) => {
        const city = cities.find((item) => item.id === group.city);
        setGroupForm({
            id: group.id,
            state: city?.state || group.city_detail?.state || '',
            city: group.city || '',
            name: group.name || '',
            description: group.description || '',
            is_active: true,
            priority: group.priority ?? 0,
        });
        setViewingGroupId(group.id);
        setGroupFormError('');
    };

    const startAssignAreas = (group) => {
        const city = cities.find((item) => item.id === group.city);
        setGroupAreaForm({
            state: city?.state || group.city_detail?.state || '',
            city: group.city || '',
            group: group.id,
            area_ids: getGroupAreaIds(group.id),
        });
        setViewingGroupId(group.id);
        setActiveTab('groupAreas');
        setGroupAreaError('');
    };




    const getApiErrorMessage = (error) => {
        const data = error?.response?.data;
        if (!data) return error?.message || 'Request failed.';
        if (typeof data === 'string') return data;
        if (data.detail) return data.detail;
        if (Array.isArray(data.name)) return data.name[0];
        if (Array.isArray(data.non_field_errors)) return data.non_field_errors[0];
        const firstValue = Object.values(data)[0];
        if (Array.isArray(firstValue)) return firstValue[0];
        if (typeof firstValue === 'string') return firstValue;
        return 'Request failed.';
    };

    const createMany = async (items, buildPayload, createFn, successLabel) => {
        setSaving(true);
        setNotice(null);
        try {
            const results = await Promise.allSettled(items.map((name) => createFn(buildPayload(name))));
            const created = results.filter((result) => result.status === 'fulfilled').length;
            const failed = results.filter((result) => result.status === 'rejected');
            const duplicateFailures = failed.filter((result) => result.reason?.response?.status === 400);
            const existing = duplicateFailures
                .map((result) => result.reason?.response?.data?.existing)
                .filter(Boolean);

            await refresh();
            if (successLabel.includes('alias')) {
                await loadAliases();
            }
            if (created && failed.length) {
                setNotice({
                    type: 'warning',
                    title: `${created} added, ${failed.length} skipped`,
                    message: duplicateFailures.length
                        ? 'Some records already exist. The list has been refreshed so you can see the saved data.'
                        : getApiErrorMessage(failed[0].reason),
                });
            } else if (failed.length) {
                if (existing[0]?.id && successLabel.includes('area')) {
                    setSelected((current) => ({ ...current, area: existing[0].id }));
                }
                setNotice({
                    type: 'warning',
                    title: `${successLabel} already exists`,
                    message: duplicateFailures.length
                        ? `${existing[0]?.name || 'This record'} is already saved. The list below has been refreshed.`
                        : getApiErrorMessage(failed[0].reason),
                });
            } else {
                setNotice({
                    type: 'success',
                    title: `${created} ${successLabel} added`,
                    message: 'Saved successfully and refreshed the list.',
                });
            }
        } catch (error) {
            console.error('Bulk create failed', error);
            setNotice({
                type: 'danger',
                title: 'Could not add location data',
                message: getApiErrorMessage(error),
            });
        } finally {
            setSaving(false);
        }
    };

    const saveGroup = async (event) => {
        event.preventDefault();
        setGroupFormError('');
        setNotice(null);

        if (!groupForm.state) {
            setGroupFormError('Select a state before saving the group.');
            return;
        }
        if (!groupForm.city) {
            setGroupFormError('Select a city before saving the group.');
            return;
        }
        if (!groupForm.name.trim()) {
            setGroupFormError('Group name is required.');
            return;
        }

        setSaving(true);
        try {
            const payload = {
                city: groupForm.city,
                name: groupForm.name.trim(),
                description: groupForm.description.trim() || null,
                is_active: true,
                priority: Number(groupForm.priority || 0),
            };
            const response = groupForm.id
                ? await locationsAPI.updateGroup(groupForm.id, payload)
                : await locationsAPI.createGroup(payload);
            const savedGroup = response.data;
            const savedGroupId = savedGroup.id || groupForm.id;
            await refresh();
            setViewingGroupId(savedGroupId);
            setSelected((current) => ({ ...current, city: groupForm.city, group: savedGroupId }));
            setNotice({
                type: 'success',
                title: groupForm.id ? 'Group updated' : 'Group created',
                message: `${payload.name} saved as an active group. Use Group Areas to assign existing areas.`,
            });
            setGroupForm({ ...emptyGroupForm, state: groupForm.state, city: groupForm.city });
        } catch (error) {
            console.error('Group save failed', error);
            setGroupFormError(getApiErrorMessage(error));
            setNotice({
                type: 'danger',
                title: 'Could not save group',
                message: getApiErrorMessage(error),
            });
        } finally {
            setSaving(false);
        }
    };

    const saveGroupAreaAssignments = async (event) => {
        event.preventDefault();
        setGroupAreaError('');
        setNotice(null);

        if (!groupAreaForm.state) {
            setGroupAreaError('Select a state before assigning areas.');
            return;
        }
        if (!groupAreaForm.city) {
            setGroupAreaError('Select a city before assigning areas.');
            return;
        }
        if (!groupAreaForm.group) {
            setGroupAreaError('Select a group before assigning areas.');
            return;
        }

        const invalidSelectedArea = groupAreaForm.area_ids
            .map((areaId) => areas.find((area) => area.id === areaId))
            .find((area) => area && area.city !== groupAreaForm.city);
        if (invalidSelectedArea) {
            setGroupAreaError(`${invalidSelectedArea.name} belongs to another city. Remove it before saving.`);
            return;
        }

        setSaving(true);
        try {
            const group = groups.find((item) => item.id === groupAreaForm.group);
            if (group && !group.is_active) {
                await locationsAPI.updateGroup(group.id, { is_active: true });
            }
            await locationsAPI.syncGroupAreas(groupAreaForm.group, { area_ids: groupAreaForm.area_ids });
            await refresh();
            setViewingGroupId(groupAreaForm.group);
            setSelected((current) => ({ ...current, city: groupAreaForm.city, group: groupAreaForm.group }));
            setNotice({
                type: 'success',
                title: 'Group areas saved',
                message: `${group?.name || 'Group'} now has ${groupAreaForm.area_ids.length} active area assignment${groupAreaForm.area_ids.length === 1 ? '' : 's'}.`,
            });
        } catch (error) {
            console.error('Group area assignment failed', error);
            setGroupAreaError(getApiErrorMessage(error));
            setNotice({
                type: 'danger',
                title: 'Could not assign areas',
                message: getApiErrorMessage(error),
            });
        } finally {
            setSaving(false);
        }
    };

    const deleteRow = async (row, deleteFn, label) => {
        if (!window.confirm(`Delete ${label} "${row.name || row.alias}"?`)) return;
        const id = getRecordId(row);
        if (!id) {
            window.alert('Delete failed. Record ID is missing.');
            return;
        }
        try {
            await deleteFn(id);
            await refresh();
        } catch (error) {
            console.error('Delete failed', error);
            const status = error?.response?.status;
            if (status === 404) {
                await refresh();
                window.alert('This record was already removed or is not available. List refreshed.');
                return;
            }
            window.alert('Delete failed.');
        }
    };

    const handleEdit = async (row, type) => {
        const id = getRecordId(row);
        if (!id) {
            window.alert('Edit failed. Record ID is missing.');
            return;
        }

        if (type === 'state') {
            const name = window.prompt('Edit state name', row.name || '');
            if (name === null) return;
            const code = window.prompt('Edit state code', row.code || '');
            const payload = {
                name: name.trim(),
                code: code?.trim() || null,
            };
            const data = {};
            if (payload.name && payload.name !== row.name) data.name = payload.name;
            if (payload.code !== (row.code || null)) data.code = payload.code;
            if (!Object.keys(data).length) return;

            setSaving(true);
            try {
                await locationsAPI.updateState(id, data);
                await refresh();
            } catch (error) {
                console.error('Edit state failed', error);
                window.alert(getApiErrorMessage(error));
            } finally {
                setSaving(false);
            }
            return;
        }

        if (type === 'city') {
            const name = window.prompt('Edit city name', row.name || '');
            if (name === null) return;
            const trimmed = name.trim();
            if (!trimmed || trimmed === row.name) return;

            setSaving(true);
            try {
                await locationsAPI.updateCity(id, { name: trimmed });
                await refresh();
            } catch (error) {
                console.error('Edit city failed', error);
                window.alert(getApiErrorMessage(error));
            } finally {
                setSaving(false);
            }
            return;
        }

        if (type === 'area') {
            const name = window.prompt('Edit area name', row.name || '');
            if (name === null) return;
            const trimmed = name.trim();
            if (!trimmed || trimmed === row.name) return;

            setSaving(true);
            try {
                await locationsAPI.updateArea(id, { name: trimmed });
                await refresh();
            } catch (error) {
                console.error('Edit area failed', error);
                window.alert(getApiErrorMessage(error));
            } finally {
                setSaving(false);
            }
        }
    };

    const bulkDeleteRows = async (rows, deleteFn, label) => {
        if (!rows.length) return;
        if (!window.confirm(`Delete ${rows.length} selected ${label}?`)) return;
        setSaving(true);
        try {
            const results = await Promise.allSettled(
                rows
                    .map((row) => getRecordId(row))
                    .filter(Boolean)
                    .map(async (id) => {
                        try {
                            await deleteFn(id);
                            return { removed: true };
                        } catch (error) {
                            if (error?.response?.status === 404) {
                                return { removed: true, alreadyMissing: true };
                            }
                            throw error;
                        }
                    })
            );
            const failed = results.filter((result) => result.status === 'rejected').length;
            const alreadyMissing = results.filter((result) => result.status === 'fulfilled' && result.value?.alreadyMissing).length;
            await refresh();
            if (failed) {
                window.alert(`${rows.length - failed} deleted. ${failed} failed because they may be missing or used by another record.`);
            } else if (alreadyMissing) {
                window.alert(`${rows.length} ${label} cleared. ${alreadyMissing} were already missing on backend.`);
            } else {
                window.alert(`${rows.length} ${label} deleted.`);
            }
        } catch (error) {
            console.error('Bulk delete failed', error);
            window.alert('Bulk delete failed.');
        } finally {
            setSaving(false);
        }
    };

    const runMatch = async (event) => {
        event.preventDefault();
        if (!matchText.trim()) return;
        setSaving(true);
        try {
            const response = await locationsAPI.match({
                text: matchText,
                state_id: selected.state || undefined,
                city_id: selected.city || undefined,
                group_id: selected.group || undefined,
            });
            setMatchResult(response.data);
        } catch (error) {
            console.error('Match failed', error);
            window.alert('Location match failed.');
        } finally {
            setSaving(false);
        }
    };

    const tabButton = (tab) => {
        const Icon = tab.icon;
        const active = activeTab === tab.id;
        return (
            <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${active ? 'bg-primary text-white' : 'bg-card text-text-secondary hover:text-text-primary'}`}
            >
                <Icon size={16} />
                {tab.label}
            </button>
        );
    };

    return (
        <div className="space-y-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Locations</h1>
                    <p className="mt-1 text-sm text-text-secondary">Manage normalized State, City, Group and Area data for branches, bots and DoubleTick.</p>
                </div>
                <Button type="button" variant="secondary" onClick={refresh} loading={loading} className="gap-2">
                    <RefreshCcw size={16} />
                    Refresh
                </Button>
            </div>

            <div className="flex flex-wrap gap-2">{tabs.map(tabButton)}</div>

            {notice && (
                <div className={`rounded-lg border px-4 py-3 ${notice.type === 'success'
                    ? 'border-success/30 bg-success/10 text-success'
                    : notice.type === 'danger'
                        ? 'border-danger/30 bg-danger/10 text-danger'
                        : 'border-warning/30 bg-warning/10 text-warning'
                    }`}>
                    <div className="flex items-start gap-3">
                        {notice.type === 'success' ? <CheckCircle2 size={18} className="mt-0.5 shrink-0" /> : <AlertTriangle size={18} className="mt-0.5 shrink-0" />}
                        <div>
                            <p className="font-semibold">{notice.title}</p>
                            <p className="text-sm opacity-90">{notice.message}</p>
                        </div>
                    </div>
                </div>
            )}

            <LocationSection icon={GitMerge} title="Working Selection" subtitle="Choose one parent, then add many child records below.">
                <LocationSelectors
                    states={states}
                    cities={selectedStateCities}
                    groups={selectedCityGroups}
                    areas={selectedCityAreas}
                    selectedState={selected.state}
                    selectedCity={selected.city}
                    selectedGroup={selected.group}
                    selectedArea={selected.area}
                    onStateChange={(value) => updateSelected('state', value)}
                    onCityChange={(value) => updateSelected('city', value)}
                    onGroupChange={(value) => updateSelected('group', value)}
                    onAreaChange={(value) => updateSelected('area', value)}
                />
            </LocationSection>

            {activeTab === 'states' && (
                <LocationSection icon={Map} title="States" subtitle="Add one state or paste multiple state names, one per line.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(520px,0.9fr)_minmax(620px,1.1fr)]">
                        <div className="space-y-5">
                            <QuickCreateForm
                                fields={[
                                    { name: 'name', label: 'State Name', placeholder: 'Maharashtra', required: true },
                                    { name: 'code', label: 'Code', placeholder: 'MH' },
                                ]}
                                loading={saving}
                                submitLabel="Add State"
                                onSubmit={(form) => createMany([form.name], () => ({ name: form.name, code: form.code, is_active: true }), locationsAPI.createState, 'state')}
                            />
                            <BulkAddBox
                                label="Multiple States"
                                placeholder={'Maharashtra\nGujarat\nRajasthan'}
                                loading={saving}
                                onSubmit={(names) => createMany(names, (name) => ({ name, is_active: true }), locationsAPI.createState, 'states')}
                            />
                        </div>
                        <LocationDataTable
                            rows={states}
                            loading={saving}                            onEdit={(row) => handleEdit(row, 'state')}                            onDelete={(row) => deleteRow(row, locationsAPI.deleteState, 'state')}
                            onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteState, label)}
                            bulkLabel="states"
                            columns={[
                                { header: 'State', accessor: 'name' },
                                { header: 'Code', render: (row) => row.code || '-' },
                                { header: 'Cities', render: (row) => row.city_count ?? '-' },
                            ]}
                        />
                    </div>
                </LocationSection>
            )}

            {activeTab === 'cities' && (
                <LocationSection icon={MapPin} title="Cities" subtitle="Select one state and add many cities under it.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(520px,0.9fr)_minmax(620px,1.1fr)]">
                        <div className="space-y-5">
                            <SearchableSelect
                                label="Parent State"
                                options={toOptions(states)}
                                value={selected.state}
                                onChange={(value) => updateSelected('state', value)}
                                placeholder="Select state first"
                            />
                            <QuickCreateForm
                                fields={[{ name: 'name', label: 'City Name', placeholder: 'Bangalore', required: true }]}
                                disabled={!selected.state}
                                loading={saving}
                                submitLabel="Add City"
                                onSubmit={(form) => createMany([form.name], (name) => ({ state: selected.state, name, is_active: true }), locationsAPI.createCity, 'city')}
                            />
                            <BulkAddBox
                                label="Multiple Cities"
                                placeholder={'Bangalore\nJaipur\nAhmedabad'}
                                disabled={!selected.state}
                                loading={saving}
                                onSubmit={(names) => createMany(names, (name) => ({ state: selected.state, name, is_active: true }), locationsAPI.createCity, 'cities')}
                            />
                        </div>
                        <LocationDataTable
                            rows={selected.state ? selectedStateCities : cities}
                            loading={saving}
                            onEdit={(row) => handleEdit(row, 'city')}
                            onDelete={(row) => deleteRow(row, locationsAPI.deleteCity, 'city')}
                            onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteCity, label)}
                            bulkLabel="cities"
                            columns={[
                                { header: 'City', accessor: 'name' },
                                { header: 'State', render: (row) => row.state_name || row.state_detail?.name || '-' },
                                { header: 'Areas', render: (row) => row.area_count ?? '-' },
                            ]}
                        />
                    </div>
                </LocationSection>
            )}

            {activeTab === 'areas' && (
                <LocationSection icon={Route} title="Areas" subtitle="Select one city and add all service areas for it.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(560px,0.9fr)_minmax(620px,1.1fr)]">
                        <div className="space-y-5">
                            <LocationSelectors
                                states={states}
                                cities={selectedStateCities}
                                groups={[]}
                                areas={[]}
                                selectedState={selected.state}
                                selectedCity={selected.city}
                                onStateChange={(value) => updateSelected('state', value)}
                                onCityChange={(value) => updateSelected('city', value)}
                                showGroup={false}
                                showArea={false}
                            />
                            <QuickCreateForm
                                fields={[{ name: 'name', label: 'Area Name', placeholder: 'Indiranagar', required: true }]}
                                disabled={!selected.city}
                                loading={saving}
                                submitLabel="Add Area"
                                onSubmit={(form) => createMany([form.name], (name) => ({ city: selected.city, name, is_active: true }), locationsAPI.createArea, 'area')}
                            />
                            <BulkAddBox
                                label="Multiple Areas"
                                placeholder={'Indiranagar\nKoramangala\nWhitefield'}
                                disabled={!selected.city}
                                loading={saving}
                                onSubmit={(names) => createMany(names, (name) => ({ city: selected.city, name, is_active: true }), locationsAPI.createArea, 'areas')}
                            />
                        </div>
                        <div className="space-y-3">
                            <div className="rounded-lg border border-border bg-card p-4">
                                <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-text-primary">
                                            {selected.city ? `${selectedCityName || 'Selected city'} areas` : 'All areas'}
                                        </p>
                                        <p className="text-xs text-text-secondary">
                                            Showing {visibleAreas.length} of {selected.city ? selectedCityAreas.length : areas.length} saved areas.
                                        </p>
                                    </div>
                                    <Input
                                        className="w-full xl:w-80"
                                        label="Find saved area"
                                        value={areaSearch}
                                        onChange={(event) => setAreaSearch(event.target.value)}
                                        placeholder="Search Alkapuri, Andheri..."
                                    />
                                </div>
                            </div>
                            <LocationDataTable
                                rows={visibleAreas}
                                loading={saving}                                onEdit={(row) => handleEdit(row, 'area')}                                onDelete={(row) => deleteRow(row, locationsAPI.deleteArea, 'area')}
                                onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteArea, label)}
                                bulkLabel="areas"
                                columns={[
                                    { header: 'Area', accessor: 'name' },
                                    { header: 'City', render: (row) => formatLocation(row.city_name || row.city_detail?.name, row.state_name || row.city_detail?.state_name) },
                                    { header: 'Groups', render: (row) => row.group_count ?? '-' },
                                ]}
                            />
                        </div>
                    </div>
                </LocationSection>
            )}

            {activeTab === 'groups' && (
                <LocationSection icon={Layers} title="Location Groups" subtitle="Create and manage city-level groups. Add areas from the separate Group Areas tab.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(560px,0.9fr)_minmax(720px,1.1fr)]">
                        <form onSubmit={saveGroup} className="space-y-5 rounded-lg border border-border bg-background p-4">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <p className="text-sm font-semibold text-text-primary">
                                        {groupForm.id ? 'Edit Location Group' : 'Create Location Group'}
                                    </p>
                                    <p className="text-xs text-text-secondary">Groups are saved active. Use Group Areas to assign multiple existing areas.</p>
                                </div>
                                <Button type="button" variant="secondary" size="sm" onClick={startCreateGroup}>
                                    New Group
                                </Button>
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                                <SearchableSelect
                                    label="State"
                                    options={toOptions(states)}
                                    value={groupForm.state}
                                    onChange={(value) => updateGroupForm('state', value)}
                                    placeholder="Select state"
                                />
                                <SearchableSelect
                                    label="City"
                                    options={toOptions(groupFormCities)}
                                    value={groupForm.city}
                                    onChange={(value) => updateGroupForm('city', value)}
                                    placeholder={groupForm.state ? 'Select city' : 'Select state first'}
                                />
                            </div>

                            <Input
                                label="Group Name"
                                value={groupForm.name}
                                onChange={(event) => updateGroupForm('name', event.target.value)}
                                placeholder="Panvel To Seawoods"
                                required
                            />

                            <div>
                                <label className="mb-1 block text-sm font-medium text-text-secondary">Description</label>
                                <textarea
                                    value={groupForm.description}
                                    onChange={(event) => updateGroupForm('description', event.target.value)}
                                    placeholder="Optional notes for this location group"
                                    className="min-h-20 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>

                            <div className="grid gap-4 md:grid-cols-[1fr_160px]">
                                <div className="rounded-lg border border-border bg-card px-3 py-2">
                                    <span className="block text-sm font-medium text-text-primary">Status</span>
                                    <span className="block text-xs text-text-secondary">New and edited groups are saved as Active.</span>
                                </div>
                                <Input
                                    label="Priority"
                                    type="number"
                                    value={groupForm.priority}
                                    onChange={(event) => updateGroupForm('priority', event.target.value)}
                                    min="0"
                                />
                            </div>

                            {groupFormError && (
                                <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{groupFormError}</p>
                            )}

                            <div className="flex flex-wrap justify-end gap-2">
                                {groupForm.id && (
                                    <Button type="button" variant="ghost" onClick={startCreateGroup}>
                                        Cancel edit
                                    </Button>
                                )}
                                <Button type="submit" loading={saving} className="gap-2">
                                    <Save size={16} />
                                    Save Group
                                </Button>
                            </div>
                        </form>

                        <div className="space-y-5">
                            <div className="rounded-lg border border-border bg-card p-4">
                                <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-text-primary">Saved Groups</p>
                                        <p className="text-xs text-text-secondary">{selected.city ? 'Filtered by selected city.' : 'Showing all saved groups.'}</p>
                                    </div>
                                    <span className="rounded-md bg-background px-2 py-1 text-xs font-semibold text-text-secondary">
                                        {(selected.city ? selectedCityGroups : groups).length} groups
                                    </span>
                                </div>
                                <LocationDataTable
                                    rows={selected.city ? selectedCityGroups : groups}
                                    loading={saving}
                                    onEdit={startEditGroup}
                                    onDelete={(row) => deleteRow(row, locationsAPI.deleteGroup, 'group')}
                                    onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteGroup, label)}
                                    bulkLabel="groups"
                                    columns={[
                                        { header: 'Group', accessor: 'name' },
                                        { header: 'City', render: (row) => formatLocation(row.city_name || row.city_detail?.name, row.state_name || row.city_detail?.state_name) },
                                        { header: 'Areas', render: (row) => row.area_count ?? row.group_areas?.length ?? '-' },
                                        {
                                            header: 'Preview',
                                            render: (row) => {
                                                const names = getGroupAreasForDisplay(row.id).map((area) => area.name).filter(Boolean);
                                                return names.length ? names.slice(0, 3).join(', ') + (names.length > 3 ? ` +${names.length - 3}` : '') : '-';
                                            },
                                        },
                                        {
                                            header: 'Open',
                                            render: (row) => (
                                                <div className="flex items-center gap-1">
                                                    <Button type="button" variant="ghost" size="sm" title="View" onClick={() => setViewingGroupId(row.id)}>
                                                        <Eye size={15} />
                                                    </Button>
                                                    <Button type="button" variant="ghost" size="sm" title="Assign areas" onClick={() => startAssignAreas(row)}>
                                                        <GitMerge size={15} />
                                                    </Button>
                                                </div>
                                            ),
                                        },
                                    ]}
                                />
                            </div>

                            <div className="rounded-lg border border-border bg-card p-4">
                                {viewingGroup ? (
                                    <div className="space-y-4">
                                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                                            <div>
                                                <p className="text-lg font-semibold text-text-primary">{viewingGroup.name}</p>
                                                <p className="text-sm text-text-secondary">{formatLocation(viewingGroup.city_detail?.name || viewingGroup.city_name, viewingGroup.city_detail?.state_name || viewingGroup.state_name)}</p>
                                            </div>
                                            <Button type="button" variant="secondary" size="sm" className="gap-2" onClick={() => startAssignAreas(viewingGroup)}>
                                                <Pencil size={15} />
                                                Add areas
                                            </Button>
                                        </div>
                                        <div className="grid gap-3 sm:grid-cols-3">
                                            <div className="rounded-lg border border-border bg-background p-3">
                                                <p className="text-xs text-text-secondary">Areas</p>
                                                <p className="text-xl font-semibold text-text-primary">{viewingGroup.area_count ?? getGroupMappings(viewingGroup.id).length}</p>
                                            </div>
                                            <div className="rounded-lg border border-border bg-background p-3">
                                                <p className="text-xs text-text-secondary">Branch coverages</p>
                                                <p className="text-xl font-semibold text-text-primary">{viewingGroup.branch_coverage_count ?? 0}</p>
                                            </div>
                                            <div className="rounded-lg border border-border bg-background p-3">
                                                <p className="text-xs text-text-secondary">Priority</p>
                                                <p className="text-xl font-semibold text-text-primary">{viewingGroup.priority ?? 0}</p>
                                            </div>
                                        </div>
                                        <div>
                                            <p className="mb-2 text-sm font-semibold text-text-primary">Assigned areas</p>
                                            {getGroupAreasForDisplay(viewingGroup.id).length ? (
                                                <div className="flex flex-wrap gap-2">
                                                    {getGroupAreasForDisplay(viewingGroup.id).map((area) => (
                                                        <span key={area.id} className="rounded-md border border-border bg-background px-2.5 py-1 text-sm text-text-primary">
                                                            {area.name}
                                                        </span>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="rounded-md border border-border bg-background px-3 py-4 text-center text-sm text-text-secondary">
                                                    No areas assigned yet.
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <p className="px-3 py-8 text-center text-sm text-text-secondary">
                                        Select View on a group to see details and assigned areas.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </LocationSection>
            )}

            {activeTab === 'groupAreas' && (
                <LocationSection icon={GitMerge} title="Add Areas To Group" subtitle="Select one active city group, then assign multiple existing areas from the same city.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(560px,0.9fr)_minmax(720px,1.1fr)]">
                        <form onSubmit={saveGroupAreaAssignments} className="space-y-5 rounded-lg border border-border bg-background p-4">
                            <div>
                                <p className="text-sm font-semibold text-text-primary">Group Area Assignment</p>
                                <p className="text-xs text-text-secondary">Assignments are saved active. Existing areas are reused; no new area records are created.</p>
                            </div>

                            <div className="grid gap-4 md:grid-cols-3">
                                <SearchableSelect
                                    label="State"
                                    options={toOptions(states)}
                                    value={groupAreaForm.state}
                                    onChange={(value) => updateGroupAreaForm('state', value)}
                                    placeholder="Select state"
                                />
                                <SearchableSelect
                                    label="City"
                                    options={toOptions(groupAreaCities)}
                                    value={groupAreaForm.city}
                                    onChange={(value) => updateGroupAreaForm('city', value)}
                                    placeholder={groupAreaForm.state ? 'Select city' : 'Select state first'}
                                />
                                <SearchableSelect
                                    label="Location Group"
                                    options={toOptions(groupAreaGroups)}
                                    value={groupAreaForm.group}
                                    onChange={(value) => updateGroupAreaForm('group', value)}
                                    placeholder={groupAreaForm.city ? 'Select group' : 'Select city first'}
                                />
                            </div>

                            <AreaMultiSelect
                                areas={groupAreaAreas}
                                selectedAreaIds={groupAreaForm.area_ids}
                                onChange={(areaIds) => updateGroupAreaForm('area_ids', areaIds)}
                                disabled={saving || !groupAreaForm.group}
                                loading={loading}
                                citySelected={Boolean(groupAreaForm.city)}
                                error={groupAreaError && groupAreaError.toLowerCase().includes('area') ? groupAreaError : ''}
                            />

                            {groupAreaError && !groupAreaError.toLowerCase().includes('area') && (
                                <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{groupAreaError}</p>
                            )}

                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <p className="text-xs text-text-secondary">
                                    {groupAreaForm.group ? `${groupAreaForm.area_ids.length} areas selected for this group.` : 'Select a group to load existing assignments.'}
                                </p>
                                <Button type="submit" loading={saving} disabled={!groupAreaForm.group} className="gap-2">
                                    <Save size={16} />
                                    Save Area Assignments
                                </Button>
                            </div>
                        </form>

                        <div className="space-y-5">
                            <div className="rounded-lg border border-border bg-card p-4">
                                <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm font-semibold text-text-primary">Current group mappings</p>
                                        <p className="text-xs text-text-secondary">Review the active area mappings created for each group.</p>
                                    </div>
                                    <span className="rounded-md bg-background px-2 py-1 text-xs font-semibold text-text-secondary">
                                        {groupAreaForm.group ? getGroupMappings(groupAreaForm.group).length : groupAreas.length} mappings
                                    </span>
                                </div>
                                <LocationDataTable
                                    rows={groupAreaForm.group ? getGroupMappings(groupAreaForm.group) : groupAreas}
                                    loading={saving}
                                    onDelete={(row) => deleteRow(row, locationsAPI.deleteGroupArea, 'group area')}
                                    onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteGroupArea, label)}
                                    bulkLabel="group area mappings"
                                    columns={[
                                        { header: 'Group', render: (row) => row.group_name || '-' },
                                        { header: 'Area', render: (row) => row.area_name || '-' },
                                        { header: 'City', render: (row) => row.city_name || '-' },
                                    ]}
                                />
                            </div>

                            <div className="rounded-lg border border-border bg-card p-4">
                                <p className="mb-3 text-sm font-semibold text-text-primary">Selected area preview</p>
                                {groupAreaForm.area_ids.length ? (
                                    <div className="flex flex-wrap gap-2">
                                        {groupAreaAreas
                                            .filter((area) => groupAreaForm.area_ids.includes(area.id))
                                            .map((area) => (
                                                <span key={area.id} className="rounded-md border border-border bg-background px-2.5 py-1 text-sm text-text-primary">
                                                    {area.name}
                                                </span>
                                            ))}
                                    </div>
                                ) : (
                                    <p className="rounded-md border border-border bg-background px-3 py-4 text-center text-sm text-text-secondary">
                                        No areas selected yet.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </LocationSection>
            )}

            {activeTab === 'aliases' && (
                <LocationSection icon={ListPlus} title="Aliases" subtitle="Add common spelling and ad-text variants for selected city or area.">
                    <div className="grid gap-5 2xl:grid-cols-[minmax(620px,0.95fr)_minmax(620px,1.05fr)]">
                        <div className="space-y-5">
                            <LocationSelectors
                                states={states}
                                cities={selectedStateCities}
                                groups={[]}
                                areas={selectedCityAreas}
                                selectedState={selected.state}
                                selectedCity={selected.city}
                                selectedArea={selected.area}
                                onStateChange={(value) => updateSelected('state', value)}
                                onCityChange={(value) => updateSelected('city', value)}
                                onAreaChange={(value) => updateSelected('area', value)}
                                showGroup={false}
                            />
                            <BulkAddBox
                                label="City Aliases"
                                placeholder={'Bengaluru\nBLR'}
                                disabled={!selected.city}
                                loading={saving}
                                onSubmit={(names) => createMany(names, (alias) => ({ city: selected.city, alias, is_active: true }), locationsAPI.createCityAlias, 'city aliases')}
                            />
                            <BulkAddBox
                                label="Area Aliases"
                                placeholder={'Indra Nagar\n100 Feet Road'}
                                disabled={!selected.area}
                                loading={saving}
                                onSubmit={(names) => createMany(names, (alias) => ({ area: selected.area, alias, is_active: true }), locationsAPI.createAreaAlias, 'area aliases')}
                            />
                        </div>
                        <div className="space-y-5">
                            <LocationDataTable
                                rows={cityAliases}
                                loading={saving}
                                onDelete={(row) => deleteRow(row, locationsAPI.deleteCityAlias, 'city alias')}
                                onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteCityAlias, label)}
                                bulkLabel="city aliases"
                                columns={[
                                    { header: 'Alias', accessor: 'alias' },
                                    { header: 'City', render: (row) => formatLocation(row.city_name, row.state_name) },
                                ]}
                            />
                            <LocationDataTable
                                rows={areaAliases}
                                loading={saving}
                                onDelete={(row) => deleteRow(row, locationsAPI.deleteAreaAlias, 'area alias')}
                                onBulkDelete={(rows, label) => bulkDeleteRows(rows, locationsAPI.deleteAreaAlias, label)}
                                bulkLabel="area aliases"
                                columns={[
                                    { header: 'Alias', accessor: 'alias' },
                                    { header: 'Area', render: (row) => formatLocation(row.area_name, row.city_name, row.state_name) },
                                ]}
                            />
                        </div>
                    </div>
                </LocationSection>
            )}

            {activeTab === 'matcher' && (
                <LocationSection icon={Search} title="Location Matcher" subtitle="Test free text before using it in bot or DoubleTick matching.">
                    <form onSubmit={runMatch} className="grid gap-4 lg:grid-cols-[1fr_auto]">
                        <Input
                            label="Customer Text"
                            value={matchText}
                            onChange={(event) => setMatchText(event.target.value)}
                            placeholder="Example: Spa near Indiranagar"
                        />
                        <div className="flex items-end">
                            <Button type="submit" loading={saving} className="gap-2">
                                <Search size={16} />
                                Match
                            </Button>
                        </div>
                    </form>
                    {matchResult && (
                        <pre className="mt-5 max-h-96 overflow-auto rounded-lg border border-border bg-background p-4 text-xs text-text-primary">
                            {JSON.stringify(matchResult, null, 2)}
                        </pre>
                    )}
                </LocationSection>
            )}
        </div>
    );
};

export default Locations;
