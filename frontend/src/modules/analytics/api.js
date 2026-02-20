import axiosInstance from '../../shared/services/axiosInstance';

export const analyticsAPI = {
    getOverview: (params) => axiosInstance.get('/analytics/overview/', { params }),
    getPeakHours: (params) => axiosInstance.get('/analytics/peak-hours/', { params }),
    // Add more analytics endpoints as backend supports them
};
