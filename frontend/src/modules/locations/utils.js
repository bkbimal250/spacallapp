export const unpackList = (response) => {
    const data = response?.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    return [];
};

export const toOptions = (items, labelBuilder) => items.map((item) => ({
    value: item.id,
    label: labelBuilder ? labelBuilder(item) : item.name,
    searchText: [
        item.name,
        item.code,
        item.state_name,
        item.city_name,
        item.normalized_name,
        item.normalized_alias,
    ].filter(Boolean).join(' '),
}));

export const linesToNames = (value) => [...new Set(
    String(value || '')
        .split(/\r?\n|,/)
        .map((item) => item.trim())
        .filter(Boolean)
)];

export const formatLocation = (...parts) => parts.filter(Boolean).join(', ') || '-';

export const activeStatus = (row) => row?.is_active === false ? 'Inactive' : 'Active';

export const getRecordId = (row) => row?.id || row?.ID || row?.uuid || row?.pk || '';
