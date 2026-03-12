import axiosInstance from '../../shared/services/axiosInstance';

export const monitoringAPI = {
    getDeviceHealth: () => axiosInstance.get('/monitoring/status/'), // Ensure this endpoint exists
    getAlerts: (params) => axiosInstance.get('/monitoring/device-events/', { params }),
    resolveAlert: (id) => axiosInstance.post(`/monitoring/device-events/${id}/resolve/`),
    resolveAllAlerts: () => axiosInstance.post('/monitoring/device-events/resolve_all/'),
    deleteAlert: (id) => axiosInstance.delete(`/monitoring/device-events/${id}/`),
};
