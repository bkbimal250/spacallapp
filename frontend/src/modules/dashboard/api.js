import axiosInstance from '../../shared/services/axiosInstance';

export const dashboardAPI = {
    getStats: (params) => axiosInstance.get('/dashboard/stats/', { params }),
    // Add other dashboard related calls here if needed, e.g. recent activity
};
