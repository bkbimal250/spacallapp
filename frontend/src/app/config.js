const getDefaultWsBaseUrl = () => {
    if (typeof window === 'undefined') return '';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
};

export const CONFIG = {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    WS_BASE_URL: import.meta.env.VITE_WS_BASE_URL || getDefaultWsBaseUrl(),
    APP_NAME: 'CallLog System',
    VERSION: '1.0.0',
};
