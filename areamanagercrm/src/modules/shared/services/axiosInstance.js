import axios from 'axios';
import { CONFIG } from '../../../app/config';
import { getToken, getRefreshToken, setToken, setRefreshToken, removeToken } from './tokenService';

const axiosInstance = axios.create({
    baseURL: CONFIG.API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

axiosInstance.interceptors.request.use(
    (config) => {
        const token = getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = getRefreshToken();

            if (refreshToken) {
                try {
                    // Attempt to negotiate a fresh token using standard SimpleJWT route
                    const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/token/refresh/`, {
                        refresh: refreshToken
                    });

                    const newAccessToken = response.data.access;
                    setToken(newAccessToken);
                    if (response.data.refresh) {
                        setRefreshToken(response.data.refresh);
                    }

                    // Reconfigure the failed request object dynamically
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

                    // Replay original request
                    return axiosInstance(originalRequest);
                } catch (refreshError) {
                    console.error("Token refresh failed", refreshError);
                    removeToken();
                    window.location.href = '/login';
                }
            } else {
                removeToken();
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default axiosInstance;
