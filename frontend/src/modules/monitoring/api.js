import axiosInstance from '../../shared/services/axiosInstance';

export const monitoringAPI = {
    getDeviceHealth: (params) => axiosInstance.get('/monitoring/status/', { params }),
    getAlerts: (params) => axiosInstance.get('/monitoring/device-events/', { params }),
    resolveAlert: (id) => axiosInstance.post(`/monitoring/device-events/${id}/resolve/`),
    resolveAllAlerts: (params) => axiosInstance.post('/monitoring/device-events/resolve_all/', null, { params }),
    deleteAlert: (id) => axiosInstance.delete(`/monitoring/device-events/${id}/`),
    deleteSelectedAlerts: (ids) => axiosInstance.post('/monitoring/device-events/delete_selected/', { ids }),
    deleteAllAlerts: (params) => axiosInstance.delete('/monitoring/device-events/delete_all/', { params }),
};
