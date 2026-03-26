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
        <div className="w-full max-w-md px-4 flex flex-col items-center">

            {/* Card */}
            <div className="w-full bg-card border border-border rounded-2xl p-6 shadow-lg">

                {/* Tabs */}
                <div className="flex bg-background p-1 rounded-xl mb-6">
                    <button
                        onClick={() => {
                            setLoginMode('password');
                            setOtpSent(false);
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${loginMode === 'password'
                                ? 'bg-primary text-white'
                                : 'text-text-secondary'
                            }`}
                    >
                        Password
                    </button>

                    <button
                        onClick={() => {
                            setLoginMode('otp');
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${loginMode === 'otp'
                                ? 'bg-primary text-white'
                                : 'text-text-secondary'
                            }`}
                    >
                        OTP
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <div className="mb-4 px-3 py-2 text-sm bg-danger/10 border border-danger/30 text-danger rounded-lg">
                        {error}
                    </div>
                )}

                {/* PASSWORD LOGIN */}
                {loginMode === 'password' ? (
                    <form onSubmit={handlePasswordLogin} className="space-y-4">

                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 outline-none"
                        />

                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 outline-none"
                        />

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold flex justify-center items-center gap-2 transition"
                        >
                            {loading ? 'Loading...' : 'Login'}
                        </button>

                    </form>
                ) : (
                    <div className="space-y-4">

                        {!otpSent ? (
                            <form onSubmit={handleRequestOTP} className="space-y-4">

                                <input
                                    type="email"
                                    placeholder="Enter Email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={requestLoading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {requestLoading ? 'Sending...' : 'Send OTP'}
                                </button>

                            </form>
                        ) : (
                            <form onSubmit={handleVerifyOTP} className="space-y-4">

                                <p className="text-sm text-text-secondary text-center">
                                    OTP sent to <span className="text-text-primary font-semibold">{email}</span>
                                </p>

                                <input
                                    type="text"
                                    maxLength="6"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    placeholder="------"
                                    className="w-full text-center text-xl tracking-widest py-3 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {loading ? 'Verifying...' : 'Verify'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setOtpSent(false)}
                                    className="text-sm text-text-muted w-full hover:text-primary transition"
                                >
                                    Change Email
                                </button>

                            </form>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <p className="mt-6 text-xs text-text-muted">
                Secure Access System
            </p>
        </div>
    );
};

export default Login;
