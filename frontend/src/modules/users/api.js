import axiosInstance from '../../shared/services/axiosInstance';

export const usersAPI = {
    getUsers: (params) => axiosInstance.get('/auth/users/', { params }),
    createUser: (data) => axiosInstance.post('/auth/users/', data),
    updateUser: (id, data) => axiosInstance.patch(`/auth/users/${id}/`, data),
    deleteUser: (id) => axiosInstance.delete(`/auth/users/${id}/`),
    getLoginHistory: (params) => axiosInstance.get('/auth/login-history/', { params }),
};
