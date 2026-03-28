import React, { useState, useEffect } from 'react';
import Button from '../../../shared/components/Button';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

const DeviceFilter = ({ onFilter }) => {

    const [selectedBranch, setSelectedBranch] = useState('');
    const [selectedCity, setSelectedCity] = useState('');
    const [selectedArea, setSelectedArea] = useState('');
    const [registrationStatus, setRegistrationStatus] = useState('');
    const [branches, setBranches] = useState([]);
    const [cities, setCities] = useState([]);
    const [areas, setAreas] = useState([]);

    useEffect(() => {
        const fetchBranches = async () => {
            try {
                const response = await branchesAPI.getBranches({ all: true });
                const branchData = response.data.results || response.data;

                setBranches(
                    branchData.map(b => ({
                        value: b.id,
                        label: b.code ? `${b.spa_name} (${b.code})` : b.spa_name,
                        title: b.spa_name
                    }))
                );

                // Extract unique cities and areas
                const uniqueCities = [...new Set(branchData.map(b => b.city).filter(Boolean))];
                const uniqueAreas = [...new Set(branchData.map(b => b.area).filter(Boolean))];

                setCities(uniqueCities.map(city => ({ value: city, label: city })));
                setAreas(uniqueAreas.map(area => ({ value: area, label: area })));

            } catch (error) {
                console.error("Failed to fetch branches for filter", error);
            }
        };

        fetchBranches();
    }, []);

    const handleFilter = () => {
        const filters = {};

        if (selectedBranch) filters.branch = selectedBranch;
        if (selectedCity) filters.city = selectedCity;
        if (selectedArea) filters.area = selectedArea;
        if (registrationStatus !== '') filters.is_registered = registrationStatus;

        onFilter(filters);
    };

    const handleClear = () => {
        setSelectedBranch('');
        setSelectedCity('');
        setSelectedArea('');
        setRegistrationStatus('');
        onFilter({});
    };

    return (

        <div className="space-y-6 text-text-primary">

            {/* 🔥 FILTER GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">

                {/* 🔥 BRANCH */}
                <div className="space-y-1">
                    <SearchableSelect
                        label="Branch"
                        placeholder="All Branches"
                        options={branches}
                        value={selectedBranch}
                        onChange={setSelectedBranch}
                        className="w-full bg-card border-border"
                    />
                </div>

                {/* city Filter */}
                <div className="space-y-1">
                    <SearchableSelect
                        label="City"
                        placeholder="All Cities"
                        options={cities}
                        value={selectedCity}
                        onChange={setSelectedCity}
                        className="w-full bg-card border-border"
                    />
                </div>

                {/* branch Area Filter */}
                <div className="space-y-1">
                    <SearchableSelect
                        label="Area"
                        placeholder="All Areas"
                        options={areas}
                        value={selectedArea}
                        onChange={setSelectedArea}
                        className="w-full bg-card border-border"
                    />
                </div>



                {/* 🔥 REGISTRATION STATUS */}
                <div className="space-y-1">
                    <label className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                        Registration Status
                    </label>

                    <select
                        className="block w-full px-3 py-2 bg-card border border-border rounded-md
                        text-text-primary text-sm
                        focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        value={registrationStatus}
                        onChange={(e) => setRegistrationStatus(e.target.value)}
                    >
                        <option value="">All</option>
                        <option value="true">Registered</option>
                        <option value="false">Pending</option>
                    </select>
                </div>

            </div>

            {/* 🔥 ACTION BUTTONS */}
            <div className="flex flex-wrap gap-3 pt-4 border-t border-border/50">

                <Button
                    variant="secondary"
                    onClick={handleClear}
                    className="px-6"
                >
                    Clear
                </Button>

                <Button
                    onClick={handleFilter}
                    className="px-8 bg-primary text-white hover:bg-primary-hover"
                >
                    Apply Filter
                </Button>

            </div>

        </div>
    );
};

export default DeviceFilter;