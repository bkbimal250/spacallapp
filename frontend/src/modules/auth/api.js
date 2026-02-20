import axiosInstance from '../../shared/services/axiosInstance';

export const authAPI = {
    login: (credentials) => axiosInstance.post('/auth/login/', credentials),
    requestOTP: (email) => axiosInstance.post('/auth/otp/request/', { email }),
    verifyOTP: (data) => axiosInstance.post('/auth/otp/verify/', data),
};
