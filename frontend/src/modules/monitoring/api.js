import axiosInstance from '../../shared/services/axiosInstance';

export const monitoringAPI = {
    getDeviceHealth: () => axiosInstance.get('/monitoring/status/'), // Ensure this endpoint exists
    getAlerts: () => axiosInstance.get('/monitoring/device-events/'), // For list of events
};
