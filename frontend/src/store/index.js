import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import branchReducer from './slices/branchSlice';
import deviceReducer from './slices/deviceSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        branch: branchReducer,
        device: deviceReducer,
    },
});
