import axiosInstance from '../../shared/services/axiosInstance';

export const branchesAPI = {
    getBranches: (params) => axiosInstance.get('/branches/', { params }),
};
