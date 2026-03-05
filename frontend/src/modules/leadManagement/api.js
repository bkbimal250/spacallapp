import axiosInstance from '../../shared/services/axiosInstance';

export const leadManagementAPI = {
    getLeads: (params) => axiosInstance.get('/leadmanagement/', { params }),
    getBranchSummary: (params) => axiosInstance.get('/leadmanagement/branch_summary/', { params }),
    getLeadDetails: (id) => axiosInstance.get(`/leadmanagement/${id}/`),
    createLead: (data) => axiosInstance.post('/leadmanagement/', data),
    updateLead: (id, data) => axiosInstance.patch(`/leadmanagement/${id}/`, data),
    deleteLead: (id) => axiosInstance.delete(`/leadmanagement/${id}/`),
};
