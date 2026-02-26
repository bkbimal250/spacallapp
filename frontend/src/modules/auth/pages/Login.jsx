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
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <div className="h-12 w-12 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-200">
                        <ShieldCheck className="h-7 w-7 text-white" />
                    </div>
                </div>
                <h2 className="mt-6 text-center text-3xl font-black text-gray-900 tracking-tight">
                    Welcome Back
                </h2>
                <p className="mt-2 text-center text-sm text-gray-500 font-medium">
                    Secure access to your CallLog Dashboard
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow-xl shadow-gray-200/50 sm:rounded-2xl sm:px-10 border border-gray-100">

                    {/* Tabs */}
                    <div className="flex p-1 bg-gray-100 rounded-xl mb-8">
                        <button
                            onClick={() => { setLoginMode('password'); setOtpSent(false); dispatch(loginFailure(null)); }}
                            className={`flex-1 flex items-center justify-center py-2 text-xs font-bold rounded-lg transition-all ${loginMode === 'password' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <Lock className="h-3.5 w-3.5 mr-2" />
                            Password
                        </button>
                        <button
                            onClick={() => { setLoginMode('otp'); dispatch(loginFailure(null)); }}
                            className={`flex-1 flex items-center justify-center py-2 text-xs font-bold rounded-lg transition-all ${loginMode === 'otp' ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            <MessageSquare className="h-3.5 w-3.5 mr-2" />
                            OTP Login
                        </button>
                    </div>

                    {error && (
                        <div className="mb-6 p-3 bg-red-50 border border-red-100 rounded-xl flex items-center text-red-600 text-xs font-bold animate-in fade-in slide-in-from-top-1">
                            <div className="h-5 w-5 rounded-full bg-red-100 flex items-center justify-center mr-2 flex-shrink-0">!</div>
                            {error}
                        </div>
                    )}

                    {loginMode === 'password' ? (
                        <form className="space-y-5" onSubmit={handlePasswordLogin}>
                            <div>
                                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-wider mb-1.5 ml-1">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                                    <input
                                        type="email"
                                        required
                                        className="w-full bg-gray-50 border-gray-100 rounded-xl pl-11 pr-4 py-2.5 border text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
                                        placeholder="admin@example.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-[11px] font-black text-gray-400 uppercase tracking-wider mb-1.5 ml-1">Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                                    <input
                                        type="password"
                                        required
                                        className="w-full bg-gray-50 border-gray-100 rounded-xl pl-11 pr-4 py-2.5 border text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
                                        placeholder="••••••••"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-indigo-200 transition-all disabled:opacity-50 flex items-center justify-center"
                            >
                                {loading ? 'Authenticating...' : (
                                    <>
                                        Sign In <ArrowRight className="ml-2 h-4 w-4" />
                                    </>
                                )}
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-5">
                            {!otpSent ? (
                                <form onSubmit={handleRequestOTP} className="space-y-5">
                                    <div>
                                        <label className="block text-[11px] font-black text-gray-400 uppercase tracking-wider mb-1.5 ml-1">Email Address</label>
                                        <div className="relative">
                                            <Mail className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                                            <input
                                                type="email"
                                                required
                                                className="w-full bg-gray-50 border-gray-100 rounded-xl pl-11 pr-4 py-2.5 border text-sm font-semibold focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
                                                placeholder="admin@example.com"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={requestLoading}
                                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-indigo-200 transition-all disabled:opacity-50 flex items-center justify-center"
                                    >
                                        {requestLoading ? 'Sending...' : 'Send OTP'}
                                    </button>
                                </form>
                            ) : (
                                <form onSubmit={handleVerifyOTP} className="space-y-5 animate-in fade-in zoom-in-95 duration-300">
                                    <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                                        <p className="text-[11px] text-indigo-700 font-bold leading-tight">
                                            OTP has been sent to <span className="underline">{email}</span>.
                                            Check your inbox.
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-[11px] font-black text-gray-400 uppercase tracking-wider mb-1.5 ml-1">OTP Code</label>
                                        <div className="relative">
                                            <Key className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                                            <input
                                                type="text"
                                                maxLength="6"
                                                required
                                                autoFocus
                                                className="w-full bg-gray-50 border-gray-100 rounded-xl pl-11 pr-4 py-2.5 border text-sm font-semibold tracking-[0.5em] focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
                                                placeholder="000000"
                                                value={otp}
                                                onChange={(e) => setOtp(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <div className="flex flex-col space-y-3">
                                        <button
                                            type="submit"
                                            disabled={loading}
                                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-indigo-200 transition-all disabled:opacity-50"
                                        >
                                            {loading ? 'Verifying...' : 'Verify & Sign In'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setOtpSent(false)}
                                            className="text-[11px] font-bold text-gray-400 hover:text-indigo-600 transition-colors uppercase tracking-widest text-center"
                                        >
                                            Change Email
                                        </button>
                                    </div>
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

