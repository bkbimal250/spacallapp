import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    notifications: [],
    onlineUsers: [],
    unreadCount: 0,
};

const notificationSlice = createSlice({
    name: 'notifications',
    initialState,
    reducers: {
        addNotification: (state, action) => {
            state.notifications.unshift({
                id: action.payload.id || Date.now(),
                ...action.payload,
                timestamp: new Date().toISOString(),
                read: false,
            });
            // Keep only the last 50 notifications to prevent performance lag
            if (state.notifications.length > 50) {
                state.notifications = state.notifications.slice(0, 50);
            }
            state.unreadCount += 1;
        },
        markAsRead: (state, action) => {
            const notification = state.notifications.find(n => n.id === action.payload);
            if (notification && !notification.read) {
                notification.read = true;
                state.unreadCount -= 1;
            }
        },
        clearNotifications: (state) => {
            state.notifications = [];
            state.unreadCount = 0;
        },
        setOnlineUsers: (state, action) => {
            state.onlineUsers = action.payload;
        },
        updateUserStatus: (state, action) => {
            const { user_id, is_online, last_seen_at } = action.payload;
            const userIndex = state.onlineUsers.findIndex(u => u.id === user_id);
            if (userIndex !== -1) {
                if (!is_online) {
                    state.onlineUsers.splice(userIndex, 1);
                }
            }
        },
        handleUserLogin: (state, action) => {
            const newUser = action.payload;
            // Add to online users if not already there
            if (!state.onlineUsers.find(u => u.id === newUser.user_id)) {
                state.onlineUsers.push({
                    id: newUser.user_id,
                    full_name: newUser.name,
                    role: newUser.role,
                    branch: newUser.branch,
                    last_login_at: newUser.time
                });
            }
        }
    },
});

export const { 
    addNotification, 
    markAsRead, 
    clearNotifications, 
    setOnlineUsers, 
    updateUserStatus,
    handleUserLogin 
} = notificationSlice.actions;

export default notificationSlice.reducer;
