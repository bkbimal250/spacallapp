import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { loginStart, loginSuccess, loginFailure } from '../../../store/slices/authSlice';
import { authAPI } from '../api';
import { setToken, setUser } from '../../../shared/services/tokenService';
import { Mail, Lock, ShieldCheck, ArrowRight, Loader2, Sparkles } from 'lucide-react';

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
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !password) return;

        dispatch(loginStart());
        try {
            const response = await authAPI.login({ email: trimmedEmail, password });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Invalid credentials'));
        }
    };

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail) return;

        setRequestLoading(true);
        dispatch(loginFailure(null));
        try {
            await authAPI.requestOTP(trimmedEmail);
            setOtpSent(true);
        } catch (err) {
            console.error("OTP Request Error:", err.response?.data);
            dispatch(loginFailure(err.response?.data?.error || 'Failed to send OTP. Please check if the user exists.'));
        } finally {
            setRequestLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !otp) return;

        dispatch(loginStart());
        try {
            const response = await authAPI.verifyOTP({ email: trimmedEmail, otp: otp.trim() });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Invalid or expired OTP'));
        }
    };

    const handleAuthSuccess = (response) => {
        const { access, refresh, user: userData } = response.data;

        if (userData && userData.role === 'branch_manager') {
            dispatch(loginFailure('Access Denied: Branch Managers must use the Android App.'));
            return;
        }

        setToken(access);
        if (refresh) {
            localStorage.setItem('refresh', refresh);
        }

        const userToStore = userData || { email: email.trim(), role: 'super_admin' };
        setUser(userToStore);
        dispatch(loginSuccess(userToStore));
        navigate('/');
    };

    return (
        <div className="w-full max-w-lg px-4 flex flex-col items-center">
            {/* Logo/Icon */}
            <div className="mb-8 p-4 bg-primary/10 rounded-2xl animate-in">
                <ShieldCheck className="h-10 w-10 text-primary" />
            </div>

            <div className="w-full glass shadow-2xl rounded-[2rem] p-8 md:p-12 border border-white/40 animate-in">
                {/* Header */}
                <div className="text-center mb-10">
                    <h1 className="text-3xl font-bold text-text-primary tracking-tight">
                        Welcome Back
                    </h1>
                    <p className="text-text-secondary mt-2 font-medium">
                        Secure access to your management dashboard
                    </p>
                </div>

                {/* Tabs */}
                <div className="flex bg-slate-100/50 p-1.5 rounded-2xl mb-8 border border-slate-200">
                    <button
                        onClick={() => {
                            setLoginMode('password');
                            setOtpSent(false);
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 ${loginMode === 'password'
                            ? 'bg-white text-primary shadow-sm'
                            : 'text-text-muted hover:text-text-secondary'
                            }`}
                    >
                        <Lock className="h-4 w-4" />
                        Password
                    </button>
                    <button
                        onClick={() => {
                            setLoginMode('otp');
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-semibold rounded-xl transition-all duration-300 ${loginMode === 'otp'
                            ? 'bg-white text-primary shadow-sm'
                            : 'text-text-muted hover:text-text-secondary'
                            }`}
                    >
                        <Mail className="h-4 w-4" />
                        OTP Flow
                    </button>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="mb-6 p-4 text-sm bg-danger/5 border border-danger/20 text-danger rounded-2xl flex items-start gap-3 animate-in">
                        <div className="mt-0.5">⚠️</div>
                        <span className="font-medium">{error}</span>
                    </div>
                )}

                {/* Form Sections */}
                {loginMode === 'password' ? (
                    <form onSubmit={handlePasswordLogin} className="space-y-5">
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-text-secondary uppercase tracking-wider ml-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-muted group-focus-within:text-primary transition-colors" />
                                <input
                                    type="email"
                                    required
                                    placeholder="admin@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-slate-200 rounded-2xl text-text-primary placeholder:text-text-muted focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-text-secondary uppercase tracking-wider ml-1">Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-muted group-focus-within:text-primary transition-colors" />
                                <input
                                    type="password"
                                    required
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-slate-200 rounded-2xl text-text-primary placeholder:text-text-muted focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-4 bg-primary hover:bg-primary-hover text-white font-bold rounded-2xl shadow-lg shadow-primary/20 transition-all active:scale-[0.98] disabled:opacity-70 disabled:active:scale-100 flex items-center justify-center gap-2 group"
                        >
                            {loading ? (
                                <Loader2 className="h-5 w-5 animate-spin" />
                            ) : (
                                <>
                                    Sign In <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                ) : (
                    <div className="space-y-6">
                        {!otpSent ? (
                            <form onSubmit={handleRequestOTP} className="space-y-5 animate-in">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-text-secondary uppercase tracking-wider ml-1">Secure Email</label>
                                    <div className="relative group">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-muted group-focus-within:text-primary transition-colors" />
                                        <input
                                            type="email"
                                            required
                                            placeholder="Verify your email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full pl-12 pr-4 py-3.5 bg-white/50 border border-slate-200 rounded-2xl text-text-primary focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={requestLoading}
                                    className="w-full py-4 bg-primary hover:bg-primary-hover text-white font-bold rounded-2xl shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2"
                                >
                                    {requestLoading ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <>Send Security Code <Sparkles className="h-4 w-4" /></>
                                    )}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleVerifyOTP} className="space-y-6 animate-in">
                                <div className="text-center">
                                    <div className="inline-block p-3 bg-info/10 text-info rounded-xl mb-4">
                                        <Mail className="h-6 w-6" />
                                    </div>
                                    <p className="text-sm text-text-secondary">
                                        We've sent a 6-digit code to <br />
                                        <span className="font-bold text-text-primary">{email}</span>
                                    </p>
                                </div>

                                <div className="space-y-4">
                                    <input
                                        type="text"
                                        maxLength="6"
                                        required
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                        placeholder="0 0 0 0 0 0"
                                        className="w-full py-4 text-center text-3xl font-extrabold tracking-[0.5em] bg-slate-50 border border-slate-200 rounded-2xl text-primary focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all placeholder:text-slate-200"
                                    />

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full py-4 bg-primary hover:bg-primary-hover text-white font-bold rounded-2xl shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2"
                                    >
                                        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Verify & Continue'}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => setOtpSent(false)}
                                        className="w-full py-2 text-sm font-semibold text-text-muted hover:text-primary transition-colors"
                                    >
                                        Incorrect email? Go back
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                )}
            </div>

            {/* Footer Info */}
            <p className="mt-12 text-sm text-text-muted font-medium flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" /> Protected by CallLog Secure Access
            </p>
        </div>
    );
};

export default Login;