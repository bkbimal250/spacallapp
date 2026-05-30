export const ROLES = {
    SUPER_ADMIN: 'super_admin',
    ADMIN: 'admin',
    AREA_MANAGER: 'area_manager',
    SPA_MANAGER: 'spa_manager',
    USER: 'user',
};

export const hasRole = (user, role) => {
    return user?.role === role;
};
