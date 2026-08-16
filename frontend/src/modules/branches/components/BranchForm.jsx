import React, { useState, useEffect, useMemo, useCallback } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../api';
import { locationsAPI } from '../../locations/api';

const BranchForm = ({ isOpen, onClose, onSubmit, initialData, saving = false }) => {

    const [formData, setFormData] = useState({
        spa_name: '',
        code: '',
        phone: '',
        shared_link: '',
        postal_code: '',
        address: '',
        is_active: true,
        branch_group: '',
        // Normalized location FK fields
        location_state: '',
        location_city: '',
        location_group: '',
        location_area: '',
    });

    const [groups, setGroups] = useState([]);

    // Cascading location options
    const [stateOptions, setStateOptions] = useState([]);
    const [cityOptions, setCityOptions] = useState([]);
    const [groupOptions, setGroupOptions] = useState([]);
    const [areaOptions, setAreaOptions] = useState([]);

    const [loadingCities, setLoadingCities] = useState(false);
    const [loadingGroups, setLoadingGroups] = useState(false);
    const [loadingAreas, setLoadingAreas] = useState(false);

    const branchGroupOptions = useMemo(() =>
        groups.map(g => ({ value: g.id, label: g.name })),
        [groups]
    );

    // Load branch groups and states on open
    useEffect(() => {
        if (!isOpen) return;

        const fetchInitial = async () => {
            try {
                const [groupsRes, statesRes] = await Promise.all([
                    branchesAPI.getGroups({ all: true }),
                    locationsAPI.getStateOptions({ is_active: true }),
                ]);
                setGroups(groupsRes.data.results || groupsRes.data || []);
                setStateOptions(statesRes.data || []);
            } catch (error) {
                console.error("Failed to fetch initial data", error);
            }
        };
        fetchInitial();
    }, [isOpen]);

    // When editing, prefetch cities/groups/areas for the stored FKs
    useEffect(() => {
        if (!isOpen) return;

        if (initialData) {
            const fd = {
                spa_name: initialData.spa_name || '',
                code: initialData.code || '',
                phone: initialData.phone || '',
                shared_link: initialData.shared_link || '',
                postal_code: initialData.postal_code || '',
                address: initialData.address || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
                branch_group: initialData.branch_group || '',
                location_state: initialData.location_state || '',
                location_city: initialData.location_city || '',
                location_group: initialData.location_group || '',
                location_area: initialData.location_area || '',
            };
            setFormData(fd);

            // Pre-fetch dependent dropdowns
            if (fd.location_state) fetchCities(fd.location_state);
            if (fd.location_city) {
                fetchGroups(fd.location_city);
                fetchAreas(fd.location_city, fd.location_group || null);
            }
        } else {
            setFormData({
                spa_name: '',
                code: '',
                phone: '',
                shared_link: '',
                postal_code: '',
                address: '',
                is_active: true,
                branch_group: '',
                location_state: '',
                location_city: '',
                location_group: '',
                location_area: '',
            });
            setCityOptions([]);
            setGroupOptions([]);
            setAreaOptions([]);
        }
    }, [initialData, isOpen]);

    const fetchCities = useCallback(async (stateId) => {
        if (!stateId) { setCityOptions([]); return; }
        setLoadingCities(true);
        try {
            const res = await locationsAPI.getCityOptions({ state: stateId, is_active: true });
            setCityOptions(res.data || []);
        } catch (e) {
            console.error("Failed to fetch cities", e);
        } finally {
            setLoadingCities(false);
        }
    }, []);

    const fetchGroups = useCallback(async (cityId) => {
        if (!cityId) { setGroupOptions([]); return; }
        setLoadingGroups(true);
        try {
            const res = await locationsAPI.getGroupOptions({ city: cityId, is_active: true });
            setGroupOptions(res.data || []);
        } catch (e) {
            console.error("Failed to fetch groups", e);
        } finally {
            setLoadingGroups(false);
        }
    }, []);

    const fetchAreas = useCallback(async (cityId, groupId) => {
        if (!cityId) { setAreaOptions([]); return; }
        setLoadingAreas(true);
        try {
            const params = { city: cityId, is_active: true };
            if (groupId) params.group = groupId;
            const res = await locationsAPI.getAreaOptions(params);
            setAreaOptions(res.data || []);
        } catch (e) {
            console.error("Failed to fetch areas", e);
        } finally {
            setLoadingAreas(false);
        }
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    // Cascading handlers for location selects
    const handleStateChange = (val) => {
        setFormData(prev => ({
            ...prev,
            location_state: val,
            location_city: '',
            location_group: '',
            location_area: '',
        }));
        setCityOptions([]);
        setGroupOptions([]);
        setAreaOptions([]);
        fetchCities(val);
    };

    const handleCityChange = (val) => {
        setFormData(prev => ({
            ...prev,
            location_city: val,
            location_group: '',
            location_area: '',
        }));
        setGroupOptions([]);
        setAreaOptions([]);
        fetchGroups(val);
        fetchAreas(val, null);
    };

    const handleGroupChange = (val) => {
        setFormData(prev => ({
            ...prev,
            location_group: val,
            location_area: '',
        }));
        setAreaOptions([]);
        fetchAreas(formData.location_city, val);
    };

    const handleAreaChange = (val) => {
        setFormData(prev => ({
            ...prev,
            location_area: val,
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const data = {
            ...formData,
            branch_group: formData.branch_group === '' ? null : formData.branch_group,
            location_state: formData.location_state === '' ? null : formData.location_state,
            location_city: formData.location_city === '' ? null : formData.location_city,
            location_group: formData.location_group === '' ? null : formData.location_group,
            location_area: formData.location_area === '' ? null : formData.location_area,
        };

        onSubmit(data);
    };

    const stateSelectOptions = useMemo(() =>
        stateOptions.map(s => ({ value: s.id, label: s.name })),
        [stateOptions]
    );
    const citySelectOptions = useMemo(() =>
        cityOptions.map(c => ({ value: c.id, label: c.name })),
        [cityOptions]
    );
    const groupSelectOptions = useMemo(() =>
        groupOptions.map(g => ({ value: g.id, label: g.name })),
        [groupOptions]
    );
    const areaSelectOptions = useMemo(() =>
        areaOptions.map(a => ({ value: a.id, label: a.name })),
        [areaOptions]
    );

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Branch' : 'Create Branch'}
        >
            <form onSubmit={handleSubmit} className="space-y-4">

                <Input
                    label="Spa Name"
                    name="spa_name"
                    value={formData.spa_name}
                    onChange={handleChange}
                    required
                />

                    <Input
                        label="Google Maps Shared Link"
                        name="shared_link"
                        type="url"
                        value={formData.shared_link}
                        onChange={handleChange}
                        placeholder="https://maps.app.goo.gl/..."
                    />
               

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                 <Input
                    label="Branch Code"
                    name="code"
                    value={formData.code}
                    onChange={handleChange}
                    required
                />
                    <Input
                        label="Branch Phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="+91..."
                    />

                </div>

                {/* ─── NORMALIZED LOCATION (cascading selects) ─── */}
                <div className="border border-border rounded-lg p-3 space-y-3">
                    <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                        📍 Spa Location (Linked)
                    </p>

                    {/* State */}
                    <SearchableSelect
                        label="State"
                        options={stateSelectOptions}
                        value={formData.location_state}
                        onChange={handleStateChange}
                        placeholder="Select State"
                    />

                    {/* City — dependent on State */}
                    <SearchableSelect
                        label={loadingCities ? "City (loading...)" : "City"}
                        options={citySelectOptions}
                        value={formData.location_city}
                        onChange={handleCityChange}
                        placeholder={formData.location_state ? "Select City" : "Select a state first"}
                        disabled={!formData.location_state || loadingCities}
                    />

                    <div className="grid grid-cols-2 gap-3">
                        {/* Location Group — dependent on City */}
                        <SearchableSelect
                            label={loadingGroups ? "Zone (loading...)" : "Zone / Group"}
                            options={groupSelectOptions}
                            value={formData.location_group}
                            onChange={handleGroupChange}
                            placeholder={formData.location_city ? "Select Zone (Optional)" : "Select a city first"}
                            disabled={!formData.location_city || loadingGroups}
                        />

                        {/* Area — dependent on City (optionally filtered by Group) */}
                        <SearchableSelect
                            label={loadingAreas ? "Area (loading...)" : "Area"}
                            options={areaSelectOptions}
                            value={formData.location_area}
                            onChange={handleAreaChange}
                            placeholder={formData.location_city ? "Select Area" : "Select a city first"}
                            disabled={!formData.location_city || loadingAreas}
                        />
                    </div>
                </div>

                {/* ─── LEGACY LOCATION FIELDS (fallback reference) ─── */}
                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="Postal Code"
                        name="postal_code"
                        type="number"
                        value={formData.postal_code}
                        onChange={handleChange}
                        required
                    />
                    <div />
                </div>

                {/* ADDRESS */}
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Address
                    </label>
                    <textarea
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        required
                        rows="3"
                        className="w-full px-3 py-2 bg-background border border-border rounded-md
                                   text-text-primary text-sm
                                   focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    />
                </div>

                {/* BRANCH GROUP */}
                <SearchableSelect
                    label="Branch Group"
                    options={branchGroupOptions}
                    value={formData.branch_group}
                    onChange={(val) => setFormData(prev => ({ ...prev, branch_group: val }))}
                    placeholder="Select Group (Optional)"
                />

                {/* STATUS */}
                <div className="flex items-center">
                    <input
                        type="checkbox"
                        id="is_active"
                        name="is_active"
                        checked={formData.is_active}
                        onChange={handleChange}
                        className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                    />
                    <label
                        htmlFor="is_active"
                        className="ml-2 text-sm text-text-primary"
                    >
                        Is Active
                    </label>
                </div>

                {/* ACTION BUTTONS */}
                <div className="flex justify-end gap-2 pt-4">
                    <Button
                        variant="secondary"
                        onClick={onClose}
                        type="button"
                        disabled={saving}
                    >
                        Cancel
                    </Button>
                    <Button type="submit" loading={saving}>
                        {initialData ? 'Update' : 'Create'}
                    </Button>
                </div>

            </form>
        </Modal>
    );
};

export default BranchForm;
