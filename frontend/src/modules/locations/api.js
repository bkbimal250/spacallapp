import axiosInstance from '../../shared/services/axiosInstance';

const list = (path, params = {}) => axiosInstance.get(`/locations/${path}/`, {
    params: { page_size: 100, compact: true, ...params },
});
const create = (path, data) => axiosInstance.post(`/locations/${path}/`, data);
const update = (path, id, data) => axiosInstance.patch(`/locations/${path}/${id}/`, data);
const remove = (path, id) => axiosInstance.delete(`/locations/${path}/${id}/`);

export const locationsAPI = {
    getStates: (params) => list('states', params),
    getStateOptions: (params) => axiosInstance.get('/locations/states/options/', { params }),
    createState: (data) => create('states', data),
    updateState: (id, data) => update('states', id, data),
    deleteState: (id) => remove('states', id),

    getCities: (params) => list('cities', params),
    getCityOptions: (params) => axiosInstance.get('/locations/cities/options/', { params }),
    createCity: (data) => create('cities', data),
    updateCity: (id, data) => update('cities', id, data),
    deleteCity: (id) => remove('cities', id),

    getCityAliases: (params) => list('city-aliases', params),
    createCityAlias: (data) => create('city-aliases', data),
    updateCityAlias: (id, data) => update('city-aliases', id, data),
    deleteCityAlias: (id) => remove('city-aliases', id),

    getAreas: (params) => list('areas', params),
    getAreaOptions: (params) => axiosInstance.get('/locations/areas/options/', { params }),
    createArea: (data) => create('areas', data),
    updateArea: (id, data) => update('areas', id, data),
    deleteArea: (id) => remove('areas', id),

    getAreaAliases: (params) => list('area-aliases', params),
    createAreaAlias: (data) => create('area-aliases', data),
    updateAreaAlias: (id, data) => update('area-aliases', id, data),
    deleteAreaAlias: (id) => remove('area-aliases', id),

    getGroups: (params) => list('groups', params),
    getGroupOptions: (params) => axiosInstance.get('/locations/groups/options/', { params }),
    createGroup: (data) => create('groups', data),
    updateGroup: (id, data) => update('groups', id, data),
    syncGroupAreas: (id, data) => axiosInstance.post(`/locations/groups/${id}/sync-areas/`, data),
    deleteGroup: (id) => remove('groups', id),

    getGroupAreas: (params) => list('group-areas', params),
    createGroupArea: (data) => create('group-areas', data),
    updateGroupArea: (id, data) => update('group-areas', id, data),
    deleteGroupArea: (id) => remove('group-areas', id),

    getBranchCoverages: (params) => list('branch-coverages', params),
    createBranchCoverage: (data) => create('branch-coverages', data),
    updateBranchCoverage: (id, data) => update('branch-coverages', id, data),
    deleteBranchCoverage: (id) => remove('branch-coverages', id),

    getIgnorePhrases: (params) => list('ignore-phrases', params),
    createIgnorePhrase: (data) => create('ignore-phrases', data),
    deleteIgnorePhrase: (id) => remove('ignore-phrases', id),

    match: (data) => axiosInstance.post('/locations/match/', data),
    analytics: () => axiosInstance.get('/locations/analytics/'),
};
