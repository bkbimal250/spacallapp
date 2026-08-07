import axios from 'axios';
import { CONFIG } from '../../app/config';
import { getToken, getRefreshToken, setToken, setRefreshToken, removeToken } from './tokenService';

const axiosInstance = axios.create({
    baseURL: CONFIG.API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

let refreshPromise = null;

const clearSessionAndRedirect = () => {
    removeToken();
    if (window.location.pathname !== '/login') {
        window.location.href = '/login';
    }
};

const refreshAccessToken = async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        throw new Error('Missing refresh token');
    }

    const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/token/refresh/`, {
        refresh: refreshToken
    });

    const newAccessToken = response.data.access;
    if (!newAccessToken) {
        throw new Error('Refresh response missing access token');
    }

    setToken(newAccessToken);
    if (response.data.refresh) {
        setRefreshToken(response.data.refresh);
    }
    return newAccessToken;
};

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

        if (error.response && error.response.status === 401 && originalRequest && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                refreshPromise = refreshPromise || refreshAccessToken();
                const newAccessToken = await refreshPromise;
                originalRequest.headers = originalRequest.headers || {};
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                return axiosInstance(originalRequest);
            } catch (refreshError) {
                console.error("Token refresh failed", refreshError);
                clearSessionAndRedirect();
            } finally {
                refreshPromise = null;
            }
        }
        return Promise.reject(error);
    }
);

export default axiosInstance;
