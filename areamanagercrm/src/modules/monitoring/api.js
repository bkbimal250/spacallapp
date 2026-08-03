import axiosInstance from '../shared/services/axiosInstance';

export const monitoringAPI = {
    summary: (minutes = 60) => axiosInstance.get('/monitoring/platform/summary/', { params: { minutes } }),
    requests: (limit = 25) => axiosInstance.get('/monitoring/platform/requests/', { params: { limit } }),
    slowQueries: (limit = 25) => axiosInstance.get('/monitoring/platform/slow-queries/', { params: { limit } }),
    health: () => axiosInstance.get('/monitoring/health/'),
};
