import axiosInstance from '../../shared/services/axiosInstance';

export const authAPI = {
    login: (credentials) => axiosInstance.post('/auth/login/', { ...credentials, client: credentials.client || 'web' }),
    requestOTP: (email) => axiosInstance.post('/auth/otp/request/', { email }),
    verifyOTP: (data) => axiosInstance.post('/auth/otp/verify/', { ...data, client: data.client || 'web' }),
    phoneOTP: (phoneNumber) => axiosInstance.post('/auth/otp/phone/request/', { phone_number: phoneNumber }),
    verifyPhoneOTP: (data) => axiosInstance.post('/auth/otp/phone/verify/', {
        phone_number: data.phone_number,
        otp: data.otp,
        client: data.client || 'web'
    }),

};
