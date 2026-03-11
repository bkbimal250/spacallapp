import axiosInstance from '../../shared/services/axiosInstance';

export const analyticsAPI = {
    getOverview: (params) => axiosInstance.get('/analytics/overview/', { params }),
    getPeakHours: (params) => axiosInstance.get('/analytics/peak-hours/', { params }),
    getStats: (params) => axiosInstance.get('/analytics/stats/', { params }),
    getCalls: (params) => axiosInstance.get('/analytics/calls/', { params }),
    getLeads: (params) => axiosInstance.get('/analytics/leads/', { params }),
};
