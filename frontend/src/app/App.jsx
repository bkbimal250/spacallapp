import React, { useEffect, useState } from 'react';
import { AppProviders } from './providers';
import { AppRoutes } from '../routes';
import { useDispatch } from 'react-redux';
import { getToken, getUser } from '../shared/services/tokenService';
import { loginSuccess } from '../store/slices/authSlice';
import '../assets/styles/global.css';

const AppContent = () => {
    const dispatch = useDispatch();
    const [isHydrating, setIsHydrating] = useState(true);

    useEffect(() => {
        const token = getToken();
        const user = getUser();
        if (token && user) {
            // Silently re-hydrate the Redux store from LocalStorage to survive page reloads
            dispatch(loginSuccess(user));
        }
        // Allow the router to mount only AFTER we've checked/injected local storage tokens
        setIsHydrating(false);
    }, [dispatch]);

    if (isHydrating) {
        return <div className="min-h-screen flex items-center justify-center bg-gray-50"><div className="animate-pulse bg-indigo-500 w-12 h-12 rounded-full"></div></div>; // Optional spinner
    }

    return <AppRoutes />;
};

const App = () => {
    return (
        <AppProviders>
            <AppContent />
        </AppProviders>
    );
};

export default App;
