import axiosInstance from '../../shared/services/axiosInstance';

export const analyticsAPI = {
    getOverview: ({ signal, ...params }) => axiosInstance.get('/analytics/overview/', { params, signal }),
    getPeakHours: ({ signal, ...params }) => axiosInstance.get('/analytics/peak-hours/', { params, signal }),
    getStats: ({ signal, ...params }) => axiosInstance.get('/analytics/stats/', { params, signal }),
    getCalls: ({ signal, ...params }) => axiosInstance.get('/analytics/calls/', { params, signal }),
    getLeads: ({ signal, ...params }) => axiosInstance.get('/analytics/leads/', { params, signal }),
};
