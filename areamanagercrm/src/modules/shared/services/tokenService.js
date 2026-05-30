export const getToken = () => localStorage.getItem('access');
export const setToken = (token) => localStorage.setItem('access', token);
export const removeToken = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
};
export const getRefreshToken = () => localStorage.getItem('refresh');
export const setRefreshToken = (token) => localStorage.setItem('refresh', token);

export const getUser = () => JSON.parse(localStorage.getItem('user'));
export const setUser = (user) => localStorage.setItem('user', JSON.stringify(user));
export const removeUser = () => localStorage.removeItem('user');
