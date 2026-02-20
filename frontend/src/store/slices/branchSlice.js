import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { branchesAPI } from '../../modules/branches/api';

// Async thunk to fetch branches
export const fetchBranches = createAsyncThunk(
    'branch/fetchBranches',
    async (_, { rejectWithValue }) => {
        try {
            const response = await branchesAPI.getBranches();
            // Handle consistent payload unpacking if nested in { results: [] }
            return response.data?.results || response.data || [];
        } catch (error) {
            return rejectWithValue(error.response?.data || error.message);
        }
    }
);

const initialState = {
    branches: [],
    loading: false,
    error: null,
};

const branchSlice = createSlice({
    name: 'branch',
    initialState,
    reducers: {
        // Additional synchronous actions can go here
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchBranches.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchBranches.fulfilled, (state, action) => {
                state.loading = false;
                state.branches = action.payload;
            })
            .addCase(fetchBranches.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export default branchSlice.reducer;
