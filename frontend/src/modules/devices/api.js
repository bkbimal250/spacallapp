import axiosInstance from '../../shared/services/axiosInstance';

export const devicesAPI = {
    getDevices: () => axiosInstance.get('/devices/'),
    getDevice: (id) => axiosInstance.get(`/devices/${id}/`),
    createDevice: (data) => axiosInstance.post('/devices/', data),
    updateDevice: (id, data) => axiosInstance.put(`/devices/${id}/`, data),
    deleteDevice: (id) => axiosInstance.delete(`/devices/${id}/`),
};
