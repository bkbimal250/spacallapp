import axiosInstance from '../../shared/services/axiosInstance';

export const callLogsAPI = {
    getCallLogs: (params) => axiosInstance.get('/calllogs/', { params }),
    // Call logs are usually read-only or created via device sync, but if needed:
    // createCallLog: (data) => axiosInstance.post('/calllogs/', data),
};
