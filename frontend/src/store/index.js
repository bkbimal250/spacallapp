import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import branchReducer from './slices/branchSlice';
import deviceReducer from './slices/deviceSlice';
import contactReducer from './slices/contactSlice';
import notificationReducer from './slices/notificationSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        branch: branchReducer,
        device: deviceReducer,
        contact: contactReducer,
        notifications: notificationReducer,
    },
});
