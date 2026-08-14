import axiosInstance from '../../shared/services/axiosInstance';

export const callRoutingAPI = {
    getRequests: (params) => axiosInstance.get('/callrouting/requests/', { params }),
    getRequest: (id) => axiosInstance.get(`/callrouting/requests/${id}/`),
    deleteRequest: (id) => axiosInstance.delete(`/callrouting/requests/${id}/`),
    getSummary: (params) => axiosInstance.get('/callrouting/requests/summary/', { params }),
    getIntegrationStatus: () => axiosInstance.get('/callrouting/requests/integration-status/'),
    getRules: (params) => axiosInstance.get('/callrouting/rules/', { params }),
};
