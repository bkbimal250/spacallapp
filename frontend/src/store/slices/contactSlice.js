import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { contactApi } from '../../modules/contacts/api';

// Async thunk to fetch contacts
export const fetchContacts = createAsyncThunk(
    'contact/fetchContacts',
    async (params, { rejectWithValue }) => {
        try {
            const response = await contactApi.getContacts(params);
            return response.data?.results || response.data || [];
        } catch (error) {
            return rejectWithValue(error.response?.data || error.message);
        }
    }
);

const initialState = {
    contacts: [],
    loading: false,
    error: null,
};

const contactSlice = createSlice({
    name: 'contact',
    initialState,
    reducers: {
        // Additional sync actions can go here
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchContacts.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(fetchContacts.fulfilled, (state, action) => {
                state.loading = false;
                state.contacts = action.payload;
            })
            .addCase(fetchContacts.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            });
    },
});

export default contactSlice.reducer;
