import axiosInstance from '../../shared/services/axiosInstance';

export const exportsAPI = {
    getExports: (params) => axiosInstance.get('/exports/', { params }),
    triggerExport: (type) => axiosInstance.post('/exports/generate/', { type }),
    downloadExport: (id) => axiosInstance.get(`/exports/${id}/download/`, { responseType: 'blob' }),
};
