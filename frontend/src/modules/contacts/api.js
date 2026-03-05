import axiosInstance from '../../shared/services/axiosInstance';

export const contactApi = {
    getContacts: (params) => axiosInstance.get('/contacts/', { params }),
    createContact: (data) => axiosInstance.post('/contacts/', data),
    updateContact: (id, data) => axiosInstance.put(`/contacts/${id}/`, data),
    deleteContact: (id) => axiosInstance.delete(`/contacts/${id}/`),
};