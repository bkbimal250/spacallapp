import axiosInstance from '../../shared/services/axiosInstance';

export const notificationsAPI = {
    getLogs: (params) => axiosInstance.get('/notifications/logs/', { params }),
    getStats: () => axiosInstance.get('/notifications/stats/'),
    sendManual: (data) => axiosInstance.post('/notifications/send-manual/', data),
};
