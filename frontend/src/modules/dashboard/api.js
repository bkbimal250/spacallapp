import axiosInstance from '../../shared/services/axiosInstance';

export const dashboardAPI = {
    getStats: () => axiosInstance.get('/dashboard/stats/'),
    // Add other dashboard related calls here if needed, e.g. recent activity
};
