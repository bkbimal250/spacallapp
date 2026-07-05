import React, { useEffect, useMemo, useState } from 'react';
import SearchableSelect from '../../../shared/components/SearchableSelect';
import { branchesAPI } from '../../branches/api';

export const toBranchOption = (branch) => {
    const area = branch.location_area_name || branch.area || '';
    const city = branch.location_city_name || branch.city || '';
    const state = branch.location_state_name || branch.state || '';
    const code = branch.code || '';
    const description = [area, city, state, code].filter(Boolean).join(' | ');

    return {
        value: String(branch.id),
        label: branch.spa_name || branch.name || code || 'Unnamed branch',
        description,
        searchText: [
            branch.spa_name,
            branch.name,
            branch.code,
            branch.area,
            branch.city,
            branch.state,
            branch.location_area_name,
            branch.location_city_name,
            branch.location_state_name,
            branch.location_group_name,
            branch.address,
            branch.phone,
        ].filter(Boolean).join(' '),
    };
};

const BranchSearchSelect = ({
    value,
    onChange,
    placeholder = 'Search branch, area, or city',
    allPlaceholder = 'All branches',
    allowEmpty = true,
    className = '',
    disabled = false,
}) => {
    const [branches, setBranches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        setLoading(true);
        setError('');
        branchesAPI.getBranches({ all: true })
            .then((res) => setBranches(res.data.results || res.data || []))
            .catch(() => {
                setBranches([]);
                setError('Unable to load branches.');
            })
            .finally(() => setLoading(false));
    }, []);

    const options = useMemo(() => branches.map(toBranchOption), [branches]);
    const displayPlaceholder = loading ? 'Loading branches...' : (allowEmpty ? allPlaceholder : placeholder);

    return (
        <div className={className}>
            <SearchableSelect
                options={options}
                value={value || ''}
                onChange={onChange}
                placeholder={displayPlaceholder}
                disabled={disabled || loading || Boolean(error) || options.length === 0}
                allowEmpty={allowEmpty}
            />
            {error && <p className="mt-1 text-xs text-danger">{error}</p>}
            {!loading && !error && options.length === 0 && (
                <p className="mt-1 text-xs text-warning">No branches found.</p>
            )}
        </div>
    );
};

export default BranchSearchSelect;
