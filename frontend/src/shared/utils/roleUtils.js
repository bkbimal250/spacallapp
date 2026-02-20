export const ROLES = {
    ADMIN: 'admin',
    USER: 'user',
};

export const hasRole = (user, role) => {
    return user?.role === role;
};
