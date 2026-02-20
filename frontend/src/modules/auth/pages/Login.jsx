import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { loginStart, loginSuccess, loginFailure } from '../../../store/slices/authSlice';
import { authAPI } from '../api';
import { setToken, setUser, setRefreshToken } from '../../../shared/services/tokenService'; // Ensure setRefreshToken is exported or handled

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { loading, error } = useSelector((state) => state.auth);

    const handleSubmit = async (e) => {
        e.preventDefault();
        dispatch(loginStart());
        try {
            const response = await authAPI.login({ email, password });
            const { access, refresh, user } = response.data; // Adjust based on actual backend response structure

            // Backend LoginView returns { refresh, access }, need to confirm if it returns user details or if we need to decode token/fetch user
            // For now, assuming standard JWT, we might need to fetch user me or decode. 
            // Looking at LoginView, it returns { refresh, access }. It does NOT return user object.
            // We should probably decoder the token or fetch user profile. 
            // For this iteration, let's just store tokens and set a dummy user or decode if possible, 
            // but better yet, let's fetch user details if needed or just redirect.

            setToken(access);
            if (refresh) {
                // Assuming we add setRefreshToken to tokenService
                localStorage.setItem('refresh', refresh);
            }

            // Minimal user info from email for now until we have a /me endpoint or similar
            const userData = { email };
            setUser(userData);

            dispatch(loginSuccess(userData));
            navigate('/');
        } catch (err) {
            console.error("Login failed", err);
            dispatch(loginFailure(err.response?.data?.error || 'Login failed'));
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-center text-3xl font-extrabold text-gray-900">
                Sign in to your account
            </h2>
            {error && <div className="text-red-500 text-center">{error}</div>}
            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                <div className="rounded-md shadow-sm -space-y-px">
                    <div>
                        <label htmlFor="email-address" className="sr-only">Email address</label>
                        <input
                            id="email-address"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                            placeholder="Email address"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <label htmlFor="password" className="sr-only">Password</label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                </div>

                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {loading ? 'Signing in...' : 'Sign in'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default Login;
