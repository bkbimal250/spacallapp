import React from 'react';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { toOptions } from '../utils';

const LocationSelectors = ({
    states = [],
    cities = [],
    groups = [],
    areas = [],
    selectedState,
    selectedCity,
    selectedGroup,
    selectedArea,
    onStateChange,
    onCityChange,
    onGroupChange,
    onAreaChange,
    showGroup = true,
    showArea = true,
}) => (
    <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-4">
        <SearchableSelect
            label="State"
            options={toOptions(states)}
            value={selectedState}
            onChange={onStateChange}
            placeholder="Select state"
            className="min-w-0"
        />
        <SearchableSelect
            label="City"
            options={toOptions(cities, (city) => `${city.name}${city.state_name ? `, ${city.state_name}` : ''}`)}
            value={selectedCity}
            onChange={onCityChange}
            placeholder="Select city"
            className="min-w-0"
        />
        {showGroup && (
            <SearchableSelect
                label="Group"
                options={toOptions(groups, (group) => `${group.name}${group.city_name ? `, ${group.city_name}` : ''}`)}
                value={selectedGroup}
                onChange={onGroupChange}
                placeholder="Select group"
                className="min-w-0"
            />
        )}
        {showArea && (
            <SearchableSelect
                label="Area"
                options={toOptions(areas, (area) => `${area.name}${area.city_name ? `, ${area.city_name}` : ''}`)}
                value={selectedArea}
                onChange={onAreaChange}
                placeholder="Select area"
                className="min-w-0"
            />
        )}
    </div>
);

export default LocationSelectors;
