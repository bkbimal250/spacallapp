import axiosInstance from '../../shared/services/axiosInstance';

export const usersAPI = {
    getUsers: (params) => axiosInstance.get('/auth/users/', { params }),
    createUser: (data) => axiosInstance.post('/auth/users/', data),
    updateUser: (id, data) => axiosInstance.put(`/auth/users/${id}/`, data), // or patch
    deleteUser: (id) => axiosInstance.delete(`/auth/users/${id}/`),
};
