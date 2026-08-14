import axiosInstance from '../../shared/services/axiosInstance';

export const branchesAPI = {
    getBranches: (params) => axiosInstance.get('/branches/', { params }),
    getBranch: (id) => axiosInstance.get(`/branches/${id}/`),
    createBranch: (data) => axiosInstance.post('/branches/', data),
    updateBranch: (id, data) => axiosInstance.put(`/branches/${id}/`, data),
    deleteBranch: (id) => axiosInstance.delete(`/branches/${id}/`),
    getOperatingHours: (id) => axiosInstance.get(`/branches/${id}/operating-hours/`),
    updateOperatingHours: (id, data) => axiosInstance.put(`/branches/${id}/operating-hours/`, data),

    // Branch Groups
    getGroups: (params) => axiosInstance.get('/branches/groups/', { params }),
    createGroup: (data) => axiosInstance.post('/branches/groups/', data),
    updateGroup: (id, data) => axiosInstance.put(`/branches/groups/${id}/`, data),
    deleteGroup: (id) => axiosInstance.delete(`/branches/groups/${id}/`),
    assignBranches: (id, branchIds) => axiosInstance.post(`/branches/groups/${id}/assign_branches/`, { branch_ids: branchIds }),

    // Branch Coverage Areas (location linking)
    getBranchCoverages: (params) => axiosInstance.get('/locations/branch-coverages/', { params }),
    createBranchCoverage: (data) => axiosInstance.post('/locations/branch-coverages/', data),
    updateBranchCoverage: (id, data) => axiosInstance.patch(`/locations/branch-coverages/${id}/`, data),
    deleteBranchCoverage: (id) => axiosInstance.delete(`/locations/branch-coverages/${id}/`),
};
