import axiosInstance from '../../shared/services/axiosInstance';

export const branchesAPI = {
    getBranches: () => axiosInstance.get('/branches/'),
    getBranch: (id) => axiosInstance.get(`/branches/${id}/`),
    createBranch: (data) => axiosInstance.post('/branches/', data),
    updateBranch: (id, data) => axiosInstance.put(`/branches/${id}/`, data),
    deleteBranch: (id) => axiosInstance.delete(`/branches/${id}/`),
};
