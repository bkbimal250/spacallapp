import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { loginStart, loginSuccess, loginFailure } from '../../../store/slices/authSlice';
import { authAPI } from '../api';
import { setToken, setUser } from '../../../shared/services/tokenService';
import { Mail, Lock, ShieldCheck, ArrowRight, MessageSquare, Key } from 'lucide-react';

const Login = () => {
    const [loginMode, setLoginMode] = useState('password'); // 'password' or 'otp'
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [requestLoading, setRequestLoading] = useState(false);

    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { loading, error } = useSelector((state) => state.auth);

    const handlePasswordLogin = async (e) => {
        e.preventDefault();
        dispatch(loginStart());
        try {
            const response = await authAPI.login({ email, password });
            handleAuthSuccess(response);
        } catch (err) {
            console.error("Login failed", err);
            dispatch(loginFailure(err.response?.data?.error || 'Invalid credentials'));
        }
    };

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        setRequestLoading(true);
        dispatch(loginFailure(null));
        try {
            await authAPI.requestOTP(email);
            setOtpSent(true);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Failed to send OTP'));
        } finally {
            setRequestLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        dispatch(loginStart());
        try {
            const response = await authAPI.verifyOTP({ email, otp });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Invalid OTP'));
        }
    };

    const handleAuthSuccess = (response) => {
        const { access, refresh, user: userData } = response.data;

        // Prevent branch_manager from accessing the web dashboard
        if (userData && userData.role === 'branch_manager') {
            dispatch(loginFailure('Access Denied: Branch Managers must use the Android App.'));
            return;
        }

        setToken(access);
        if (refresh) {
            localStorage.setItem('refresh', refresh);
        }
        const userToStore = userData || { email, role: 'super_admin' };
        setUser(userToStore);
        dispatch(loginSuccess(userToStore));
        navigate('/');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-indigo-100 px-4">

            {/* Main Card */}
            <div className="w-full max-w-md">


                {/* Card */}
                <div className="bg-white/80 backdrop-blur-xl border border-gray-200 shadow-2xl rounded-3xl p-8">

                    {/* Tabs */}
                    <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
                        <button
                            onClick={() => {
                                setLoginMode("password");
                                setOtpSent(false);
                                dispatch(loginFailure(null));
                            }}
                            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${loginMode === "password"
                                ? "bg-white shadow text-indigo-600"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                        >
                            Password
                        </button>

                        <button
                            onClick={() => {
                                setLoginMode("otp");
                                dispatch(loginFailure(null));
                            }}
                            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${loginMode === "otp"
                                ? "bg-white shadow text-indigo-600"
                                : "text-gray-500 hover:text-gray-700"
                                }`}
                        >
                            OTP Login
                        </button>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Password Login */}
                    {loginMode === "password" ? (
                        <form onSubmit={handlePasswordLogin} className="space-y-5">

                            {/* Email */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Email
                                </label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                    <input
                                        type="email"
                                        required
                                        placeholder="admin@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm"
                                    />
                                </div>
                            </div>

                            {/* Password */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Password
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                    <input
                                        type="password"
                                        required
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm"
                                    />
                                </div>
                            </div>

                            {/* Button */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all shadow-lg hover:shadow-indigo-300 disabled:opacity-50"
                            >
                                {loading ? "Authenticating..." : "Sign In"}
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-5">
                            {!otpSent ? (
                                <form onSubmit={handleRequestOTP} className="space-y-5">

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Email
                                        </label>
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                                            <input
                                                type="email"
                                                required
                                                placeholder="admin@example.com"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm"
                                            />
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={requestLoading}
                                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all shadow-lg disabled:opacity-50"
                                    >
                                        {requestLoading ? "Sending..." : "Send OTP"}
                                    </button>
                                </form>
                            ) : (
                                <form onSubmit={handleVerifyOTP} className="space-y-5">

                                    <div className="bg-indigo-50 border border-indigo-200 p-3 rounded-xl text-sm text-indigo-700">
                                        OTP sent to <span className="font-semibold">{email}</span>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            OTP Code
                                        </label>
                                        <input
                                            type="text"
                                            maxLength="6"
                                            value={otp}
                                            onChange={(e) => setOtp(e.target.value)}
                                            className="w-full py-2.5 px-4 rounded-xl border border-gray-300 text-center tracking-[0.4em] text-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                            placeholder="000000"
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all shadow-lg disabled:opacity-50"
                                    >
                                        {loading ? "Verifying..." : "Verify & Sign In"}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => setOtpSent(false)}
                                        className="w-full text-xs text-gray-500 hover:text-indigo-600 font-medium"
                                    >
                                        Change Email
                                    </button>
                                </form>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Login;

