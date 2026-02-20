import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { devicesAPI } from '../../modules/devices/api';

// Async thunk to fetch devices
export const fetchDevices = createAsyncThunk(
    'device/fetchDevices',
    async (_, { rejectWithValue }) => {
        try {
            const response = await devicesAPI.getDevices();
            return response.data?.results || response.data || [];
        } catch (error) {
            return rejectWithValue(error.response?.data || error.message);
        }
    }
);

const initialState = {
    devices: [],
    loading: false,
    error: null,
};

const deviceSlice = createSlice({
    name: 'device',
    initialState,
    reducers: {
        // Additional synchronous actions can go here
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchDevices.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchDevices.fulfilled, (state, action) => {
                state.loading = false;
                state.devices = action.payload;
            })
            .addCase(fetchDevices.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export default deviceSlice.reducer;
