import axiosInstance from '../../shared/services/axiosInstance';

export const devicesAPI = {
    getDevices: (params) => axiosInstance.get('/devices/', { params }),
    getDevice: (id) => axiosInstance.get(`/devices/${id}/`),
    createDevice: (data) => axiosInstance.post('/devices/', data),
    updateDevice: (id, data) => axiosInstance.put(`/devices/${id}/`, data),
    deleteDevice: (id) => axiosInstance.delete(`/devices/${id}/`),
    getDeviceStats: () => axiosInstance.get('/devices/stats/'),
    regenerateToken: (id) => axiosInstance.post(`/devices/${id}/regenerate_token/`),
};
