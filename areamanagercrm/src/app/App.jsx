import React, { useEffect, useMemo, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import DashboardLayout from '../layouts/DashboardLayout';
import Login from '../modules/auth/pages/Login';
import CallLogList from '../modules/auth/calllogs/pages/CallLogList';
import CallLogSummary from '../modules/auth/calllogs/pages/CallLogSummary';
import { getToken, getUser, removeToken, removeUser, setToken, setUser } from '../modules/shared/services/tokenService';

export const AuthContext = React.createContext(null);

const App = () => {
    const [auth, setAuth] = useState({
        token: null,
        user: null,
        ready: false,
    });

    useEffect(() => {
        setAuth({
            token: getToken(),
            user: getUser(),
            ready: true,
        });
    }, []);

    const authValue = useMemo(() => ({
        user: auth.user,
        token: auth.token,
        isAuthenticated: Boolean(auth.token && auth.user),
        login: ({ access, refresh, user }) => {
            setToken(access);
            if (refresh) {
                localStorage.setItem('refresh', refresh);
            }
            setUser(user);
            setAuth({ token: access, user, ready: true });
        },
        logout: () => {
            removeToken();
            removeUser();
            setAuth({ token: null, user: null, ready: true });
        },
    }), [auth.token, auth.user]);

    if (!auth.ready) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background text-textSecondary">
                Loading dashboard...
            </div>
        );
    }

    return (
        <AuthContext.Provider value={authValue}>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={authValue.isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
                    <Route element={authValue.isAuthenticated ? <DashboardLayout /> : <Navigate to="/login" replace />}>
                        <Route index element={<CallLogSummary />} />
                        <Route path="/calllogs" element={<CallLogList />} />
                    </Route>
                    <Route path="*" element={<Navigate to={authValue.isAuthenticated ? '/' : '/login'} replace />} />
                </Routes>
            </BrowserRouter>
        </AuthContext.Provider>
    );
};

export default App;
