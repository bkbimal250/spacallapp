import axiosInstance from '../../shared/services/axiosInstance';

export const branchesAPI = {
    getBranches: (params) => axiosInstance.get('/branches/', { params }),
    getBranch: (id) => axiosInstance.get(`/branches/${id}/`),
    createBranch: (data) => axiosInstance.post('/branches/', data),
    updateBranch: (id, data) => axiosInstance.put(`/branches/${id}/`, data),
    deleteBranch: (id) => axiosInstance.delete(`/branches/${id}/`),
    
    // Branch Groups
    getGroups: (params) => axiosInstance.get('/branches/groups/', { params }),
    createGroup: (data) => axiosInstance.post('/branches/groups/', data),
    updateGroup: (id, data) => axiosInstance.put(`/branches/groups/${id}/`, data),
    deleteGroup: (id) => axiosInstance.delete(`/branches/groups/${id}/`),
    assignBranches: (id, branchIds) => axiosInstance.post(`/branches/groups/${id}/assign_branches/`, { branch_ids: branchIds }),
};
