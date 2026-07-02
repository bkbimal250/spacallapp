import axiosInstance from '../../shared/services/axiosInstance';

export const exportsAPI = {
    getExports: (params) => axiosInstance.get('/exports/', { params }),
    triggerExport: (data) => axiosInstance.post('/exports/generate/', data),
    downloadExport: (id) => axiosInstance.get(`/exports/${id}/download/`, { responseType: 'blob' }),
    deleteExport: (id) => axiosInstance.delete(`/exports/${id}/`),
};
